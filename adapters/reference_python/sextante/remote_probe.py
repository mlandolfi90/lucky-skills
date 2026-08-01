from __future__ import annotations

import hashlib
import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit, urlunsplit

from .authority import is_human_actor
from .command import GitClient, query_http_remote_ref
from .git_ref import branch_to_ref
from .models import LocalObservation, RemoteObservation


REDIRECT_POLICY = "DENY"
MAX_REMOTE_URL_LENGTH = 2048
SOURCE_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
OID_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


@dataclass(frozen=True)
class RemoteEndpoint:
    status: str
    display_url: str
    query_url: str = ""


@dataclass(frozen=True)
class ResolvedRemoteSource:
    name: str
    url: str
    ref: str
    source_id: str
    candidates: tuple[str, ...]

    def observation(
        self,
        *,
        result: str,
        state: str,
        head: str = "UNKNOWN",
        query_attempted: bool = False,
    ) -> RemoteObservation:
        return RemoteObservation(
            result=result,
            state=state,
            name=self.name,
            url=self.url,
            head=head,
            ref=self.ref,
            source_id=self.source_id,
            redirect_policy=REDIRECT_POLICY,
            query_attempted=query_attempted,
            candidates=self.candidates,
            evidence_level="VERIFIED_DIRECT",
        )


def probe_remote(
    *,
    git: GitClient,
    local: LocalObservation,
    selected_remote: str,
    network_confirmed_by: str,
    confirmed_source_id: str,
) -> RemoteObservation:
    if not git.available:
        return RemoteObservation(result="PARTIAL", state="GIT_UNAVAILABLE")
    if local.versioning == "UNVERSIONED":
        return RemoteObservation(
            result="NOT_APPLICABLE",
            state="NO_GIT",
            ref="NOT_APPLICABLE",
            source_id="NOT_APPLICABLE",
            evidence_level="VERIFIED_DIRECT",
        )

    remotes_result = git.query("remote")
    if remotes_result.timed_out:
        return RemoteObservation(result="PARTIAL", state="TIMEOUT")
    if remotes_result.output_limited:
        return RemoteObservation(result="PARTIAL", state="OUTPUT_LIMIT")
    if remotes_result.returncode != 0:
        return RemoteObservation(result="PARTIAL", state="UNREACHABLE")

    remotes = tuple(
        sorted(
            name.strip() for name in remotes_result.stdout.splitlines() if name.strip()
        )
    )
    if not remotes:
        return RemoteObservation(
            result="NOT_APPLICABLE",
            state="NO_REMOTE",
            ref="NOT_APPLICABLE",
            source_id="NOT_APPLICABLE",
            evidence_level="VERIFIED_DIRECT",
        )

    if selected_remote in {"", "AUTO"}:
        if len(remotes) > 1:
            return RemoteObservation(
                result="PARTIAL",
                state="MULTIPLE_CANDIDATES",
                candidates=remotes,
                evidence_level="VERIFIED_DIRECT",
            )
        remote_name = remotes[0]
    elif selected_remote not in remotes:
        return RemoteObservation(
            result="PARTIAL",
            state="UNKNOWN_SELECTION",
            candidates=remotes,
            evidence_level="VERIFIED_DIRECT",
        )
    else:
        remote_name = selected_remote

    url_result = git.query("config", "--get-all", f"remote.{remote_name}.url")
    if url_result.output_limited:
        return RemoteObservation(
            result="PARTIAL",
            state="OUTPUT_LIMIT",
            name=remote_name,
        )
    if url_result.returncode != 0:
        return RemoteObservation(
            result="PARTIAL",
            state="URL_UNAVAILABLE",
            name=remote_name,
        )
    configured_urls = tuple(
        value.strip() for value in url_result.stdout.splitlines() if value.strip()
    )
    if len(configured_urls) != 1:
        return RemoteObservation(
            result="PARTIAL",
            state="MULTIPLE_URLS",
            name=remote_name,
            candidates=remotes,
            evidence_level="VERIFIED_DIRECT",
        )

    endpoint = classify_http_endpoint(configured_urls[0])
    if endpoint.status != "SAFE":
        return RemoteObservation(
            result="PARTIAL",
            state=endpoint.status,
            name=remote_name,
            url=endpoint.display_url,
            candidates=remotes,
            evidence_level="VERIFIED_DIRECT",
        )

    remote_ref = branch_to_ref(local.branch)
    if remote_ref == "UNKNOWN":
        return RemoteObservation(
            result="PARTIAL",
            state="LOCAL_BRANCH_UNAVAILABLE",
            name=remote_name,
            url=endpoint.display_url,
            candidates=remotes,
            evidence_level="VERIFIED_DIRECT",
        )
    source_id = remote_source_id(
        workspace_path=str(git.workspace),
        remote_name=remote_name,
        query_url=endpoint.query_url,
        remote_ref=remote_ref,
    )
    source = ResolvedRemoteSource(
        name=remote_name,
        url=endpoint.display_url,
        ref=remote_ref,
        source_id=source_id,
        candidates=remotes,
    )
    if not is_human_actor(network_confirmed_by) or not confirmed_source_id:
        return source.observation(
            result="PARTIAL",
            state="NETWORK_CONFIRMATION_REQUIRED",
        )
    if confirmed_source_id != source_id:
        return source.observation(
            result="PARTIAL",
            state="SOURCE_CONFIRMATION_MISMATCH",
        )

    ref_result = query_http_remote_ref(
        endpoint.query_url,
        remote_ref,
        timeout_seconds=git.timeout_seconds,
    )
    if ref_result.timed_out:
        return source.observation(
            result="PARTIAL",
            state="TIMEOUT",
            query_attempted=True,
        )
    if ref_result.output_limited:
        return source.observation(
            result="PARTIAL",
            state="OUTPUT_LIMIT",
            query_attempted=True,
        )
    if ref_result.returncode != 0:
        state = "REF_NOT_FOUND" if ref_result.returncode == 2 else "UNREACHABLE"
        return source.observation(
            result="PARTIAL",
            state=state,
            query_attempted=True,
        )

    remote_head = _parse_remote_ref(ref_result.stdout, expected_ref=remote_ref)
    if remote_head is None:
        return source.observation(
            result="PARTIAL",
            state="REMOTE_RESPONSE_INVALID",
            query_attempted=True,
        )

    result = "ALIGNED"
    if local.head not in {"NO_COMMIT", "NOT_APPLICABLE", "UNKNOWN"}:
        if remote_head != local.head:
            result = "DRIFT"
    elif local.head == "NO_COMMIT":
        result = "DRIFT"

    return source.observation(
        result=result,
        state="VERIFIED",
        head=remote_head,
        query_attempted=True,
    )


def classify_http_endpoint(value: str) -> RemoteEndpoint:
    fallback = _redacted_display(value)
    if not value or len(value) > MAX_REMOTE_URL_LENGTH or "\0" in value:
        return RemoteEndpoint("MALFORMED_URL", fallback)
    try:
        parsed = urlsplit(value)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        port = parsed.port
        username = parsed.username
        password = parsed.password
    except ValueError:
        return RemoteEndpoint("MALFORMED_URL", fallback)
    if scheme not in {"http", "https"}:
        return RemoteEndpoint("UNSUPPORTED_SAFE_TRANSPORT", fallback)
    if any(character.isspace() for character in value) or not hostname:
        return RemoteEndpoint("MALFORMED_URL", fallback)
    if username is not None or password is not None or "?" in value or "#" in value:
        return RemoteEndpoint("UNSAFE_URL_COMPONENTS", fallback)
    if port is not None and not 1 <= port <= 65535:
        return RemoteEndpoint("MALFORMED_URL", fallback)
    normalized_host = hostname.rstrip(".").lower()
    if normalized_host == "localhost" or normalized_host.endswith(".localhost"):
        return RemoteEndpoint("UNSUPPORTED_SAFE_TRANSPORT", fallback)
    try:
        address = ipaddress.ip_address(normalized_host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        return RemoteEndpoint("UNSUPPORTED_SAFE_TRANSPORT", fallback)
    return RemoteEndpoint("SAFE", value, value)


def redact_remote_url(value: str) -> str:
    return _redacted_display(value)


def valid_source_id(value: str) -> bool:
    return bool(SOURCE_ID_PATTERN.fullmatch(value))


def _redacted_display(value: str) -> str:
    if not value:
        return "UNKNOWN"
    if "://" not in value:
        if "@" in value and ":" in value:
            host, _, path = value.split("@", 1)[-1].partition(":")
            return f"ssh://{host}/{path}"
        scheme = value.split(":", 1)[0].lower()
        return f"{scheme}:REDACTED" if scheme else "UNSUPPORTED:REDACTED"
    try:
        parsed = urlsplit(value)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        scheme = value.split(":", 1)[0].lower()
        return f"{scheme}:REDACTED" if scheme else "MALFORMED:REDACTED"
    if scheme not in {"http", "https", "ssh", "git"} or not hostname:
        return f"{scheme}:REDACTED" if scheme else "UNSUPPORTED:REDACTED"
    host = f"[{hostname}]" if ":" in hostname else hostname
    netloc = f"{host}:{port}" if port else host
    return urlunsplit(
        SplitResult(
            scheme=scheme,
            netloc=netloc,
            path=parsed.path,
            query="",
            fragment="",
        )
    )


def remote_source_id(
    *,
    workspace_path: str,
    remote_name: str,
    query_url: str,
    remote_ref: str,
) -> str:
    material = "\0".join(
        (
            "sextante-remote-source-v1",
            workspace_path,
            remote_name,
            query_url,
            remote_ref,
            REDIRECT_POLICY,
        )
    )
    return f"sha256:{hashlib.sha256(material.encode('utf-8')).hexdigest()}"


def _parse_remote_ref(output: str, *, expected_ref: str) -> str | None:
    lines = tuple(line for line in output.splitlines() if line)
    if len(lines) != 1:
        return None
    oid, separator, observed_ref = lines[0].partition("\t")
    if not separator or observed_ref != expected_ref or not OID_PATTERN.fullmatch(oid):
        return None
    return oid
