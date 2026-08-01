from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import patch

from support import ADAPTER_ROOT, ROOT, VERSION, AdapterHarness
from sextante import cli
from sextante.bounded_process import ProcessResult
from sextante.command import CommandResult, GitClient, query_http_remote_ref
from sextante.envfile import load_env
from sextante.local_probe import probe_local
from sextante.receipt import verify_receipt
from sextante.remote_probe import classify_http_endpoint, probe_remote


class GitSafetyTests(AdapterHarness):
    def test_local_git_queries_disable_lazy_fetch_and_replace_objects(self) -> None:
        completed = ProcessResult(0, "", "", False, False)
        with (
            patch.dict(
                os.environ,
                {"GIT_OBJECT_DIRECTORY": "untrusted-object-store"},
                clear=False,
            ),
            patch(
                "sextante.command.run_bounded_process",
                return_value=completed,
            ) as bounded,
        ):
            GitClient(self.workspace, timeout_seconds=5).query(
                "rev-parse",
                "--verify",
                "HEAD",
            )

        environment = bounded.call_args.kwargs["environment"]
        self.assertNotIn("GIT_OBJECT_DIRECTORY", environment)
        self.assertEqual(environment["GIT_NO_LAZY_FETCH"], "1")
        self.assertEqual(environment["GIT_NO_REPLACE_OBJECTS"], "1")

    def test_remote_query_disables_redirects_and_requests_one_exact_ref(
        self,
    ) -> None:
        completed = ProcessResult(0, "", "", False, False)
        with patch(
            "sextante.command.run_bounded_process",
            return_value=completed,
        ) as bounded:
            query_http_remote_ref(
                "https://example.test/repo.git",
                "refs/heads/feature/x",
                timeout_seconds=5,
            )

        arguments = tuple(bounded.call_args.args[0])
        self.assertIn("http.followRedirects=false", arguments)
        self.assertIn("--refs", arguments)
        self.assertEqual(
            arguments[-2:],
            (
                "https://example.test/repo.git",
                "refs/heads/feature/x",
            ),
        )

    def test_repository_clean_filter_is_not_executed(self) -> None:
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Sextante Test")
        self.git("config", "user.email", "sextante@example.invalid")
        marker = self.base / "clean-filter-invoked"
        filter_script = self.base / "clean-filter.sh"
        filter_script.write_text(
            "#!/bin/sh\n" f"printf invoked > '{marker.as_posix()}'\n" "cat\n",
            encoding="utf-8",
        )
        filter_script.chmod(0o755)
        self.git("config", "filter.evil.clean", filter_script.as_posix())
        self.git("config", "filter.evil.required", "true")
        (self.workspace / ".gitattributes").write_text(
            "*.txt filter=evil\n", encoding="utf-8"
        )
        payload = self.workspace / "payload.txt"
        payload.write_text("initial\n", encoding="utf-8")
        self.git("add", ".gitattributes", "payload.txt")
        self.git("commit", "-m", "test: hostile clean filter")
        self.assertTrue(marker.is_file(), "la precondición hostil no se ejecutó")
        marker.unlink()
        payload.write_text("changed\n", encoding="utf-8")

        self.git("status", "--porcelain")
        self.assertTrue(marker.is_file(), "git status no reprodujo la ejecución")
        marker.unlink()

        _, receipt = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|git|INVOKABLE|UNKNOWN",
        )

        self.assertFalse(marker.exists())
        self.assertEqual(receipt["LOCAL_DIRTY"], "TRUE")
        self.assertEqual(
            receipt["LOCAL_DIRTY_MODE"],
            "RAW_NO_FILTERS_CONSERVATIVE",
        )

    def test_repository_fsmonitor_is_not_executed(self) -> None:
        self.init_committed_repository()
        marker = self.base / "fsmonitor-invoked"
        hook = self.base / "fsmonitor-hook.sh"
        hook.write_text(
            "#!/bin/sh\n"
            f"printf invoked > '{marker.as_posix()}'\n"
            "printf '2\\n\\n'\n",
            encoding="utf-8",
        )
        hook.chmod(0o755)
        self.git("config", "core.fsmonitor", hook.as_posix())

        self.git("status", "--porcelain")
        self.assertTrue(marker.is_file(), "la precondición hostil no se ejecutó")
        marker.unlink()

        self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|git|INVOKABLE|UNKNOWN",
        )

        self.assertFalse(marker.exists())

    def test_ext_remote_is_neither_executed_nor_persisted_raw(self) -> None:
        self.git("init", "-b", "main")
        marker = self.base / "remote-helper-invoked"
        hostile = f"ext::sh -c 'printf invoked > {marker.as_posix()}'"
        self.git("remote", "add", "origin", hostile)

        _, receipt = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|git|INVOKABLE|UNKNOWN",
        )

        self.assertFalse(marker.exists())
        self.assertEqual(receipt["REMOTE_STATE"], "UNSUPPORTED_SAFE_TRANSPORT")
        self.assertEqual(receipt["REMOTE_URL"], "ext:REDACTED")
        self.assertNotIn("printf invoked", self.last_receipt_path().read_text("utf-8"))

    def test_literal_local_network_remote_is_not_contacted(self) -> None:
        self.git("init", "-b", "main")
        self.git("remote", "add", "origin", "http://127.0.0.1:9/repo.git")

        _, receipt = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|git|INVOKABLE|UNKNOWN",
        )

        self.assertEqual(receipt["REMOTE_STATE"], "UNSUPPORTED_SAFE_TRANSPORT")

    def test_dns_remote_requires_human_before_any_network_call(self) -> None:
        self.git("init", "-b", "main")
        self.git(
            "remote",
            "add",
            "origin",
            "http://127.0.0.1.nip.io:9/repo.git",
        )
        local, git = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )

        with patch(
            "sextante.remote_probe.query_http_remote_ref",
            side_effect=AssertionError("network call must not happen"),
        ):
            observation = probe_remote(
                git=git,
                local=local,
                selected_remote="AUTO",
                network_confirmed_by="",
                confirmed_source_id="",
            )

        self.assertEqual(
            observation.state,
            "NETWORK_CONFIRMATION_REQUIRED",
        )
        summary, receipt = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|git|INVOKABLE|UNKNOWN",
        )
        self.assertEqual(
            receipt["REMOTE_STATE"],
            "NETWORK_CONFIRMATION_REQUIRED",
        )
        self.assertEqual(
            receipt["REMOTE_QUERY_CONFIRMED_BY"],
            "UNCONFIRMED",
        )
        self.assertEqual(
            summary["HUMAN_DECISION"],
            "CONFIRM_SOURCE_ACCESS",
        )

    def test_malformed_remote_urls_never_reach_network_query(self) -> None:
        for raw_url in (
            "https://[broken/repo.git",
            "https://example.test:bad/repo.git",
        ):
            with self.subTest(raw_url=raw_url):
                endpoint = classify_http_endpoint(raw_url)
                self.assertEqual(endpoint.status, "MALFORMED_URL")
                self.assertFalse(endpoint.query_url)

    def test_remote_confirmation_is_bound_to_url_branch_and_workspace(self) -> None:
        self.init_committed_repository()
        self.git("switch", "-c", "feature/x")
        self.git("remote", "add", "origin", "https://example.test/repo.git")
        local, git = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )
        pending = probe_remote(
            git=git,
            local=local,
            selected_remote="AUTO",
            network_confirmed_by="",
            confirmed_source_id="",
        )
        self.assertEqual(pending.state, "NETWORK_CONFIRMATION_REQUIRED")
        response = CommandResult(
            0,
            f"{local.head}\trefs/heads/feature/x\n",
            "",
        )

        with patch(
            "sextante.remote_probe.query_http_remote_ref",
            return_value=response,
        ) as query:
            verified = probe_remote(
                git=git,
                local=local,
                selected_remote="AUTO",
                network_confirmed_by="human:owner",
                confirmed_source_id=pending.source_id,
            )

        self.assertEqual(verified.result, "ALIGNED")
        self.assertEqual(verified.ref, "refs/heads/feature/x")
        self.assertTrue(verified.query_attempted)
        query.assert_called_once_with(
            "https://example.test/repo.git",
            "refs/heads/feature/x",
            timeout_seconds=5,
        )

        self.git(
            "config",
            "remote.origin.url",
            "https://example.test/changed.git",
        )
        with patch(
            "sextante.remote_probe.query_http_remote_ref",
            side_effect=AssertionError("stale confirmation must not query"),
        ):
            changed = probe_remote(
                git=git,
                local=local,
                selected_remote="AUTO",
                network_confirmed_by="human:owner",
                confirmed_source_id=pending.source_id,
            )
        self.assertEqual(changed.state, "SOURCE_CONFIRMATION_MISMATCH")
        self.assertFalse(changed.query_attempted)

    def test_safe_global_ipv6_keeps_brackets_and_port(self) -> None:
        raw_url = "https://[2606:4700:4700::1111]:8443/repo.git"

        endpoint = classify_http_endpoint(raw_url)

        self.assertEqual(endpoint.status, "SAFE")
        self.assertEqual(endpoint.query_url, raw_url)
        self.assertEqual(endpoint.display_url, raw_url)

    def test_confirmed_exact_remote_ref_can_enable_matching_push(self) -> None:
        self.init_committed_repository()
        self.git("remote", "add", "origin", "https://example.test/repo.git")
        local, git = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )
        pending = probe_remote(
            git=git,
            local=local,
            selected_remote="AUTO",
            network_confirmed_by="",
            confirmed_source_id="",
        )
        arguments = cli._parser().parse_args(
            [
                "--workspace",
                str(self.workspace),
                "--receipt-root",
                str(self.receipt_root),
                "--remote-confirmed-by",
                "human:owner",
                "--remote-confirmed-source-id",
                pending.source_id,
                "--runtime-result",
                "NOT_APPLICABLE",
                "--runtime-source",
                "fixture:no-runtime",
                "--runtime-evidence",
                "VERIFIED_DIRECT",
                "--capability",
                "tool|git-push|INVOKABLE|UNKNOWN",
                "--intent",
                "push",
                "--target-where",
                "remote:origin:refs/heads/main",
                "--target-action",
                "PUSH",
                "--target-confirmed-by",
                "human:owner",
            ]
        )
        response = CommandResult(
            0,
            f"{local.head}\trefs/heads/main\n",
            "",
        )

        with patch(
            "sextante.remote_probe.query_http_remote_ref",
            return_value=response,
        ):
            result = cli.run_check(
                arguments=arguments,
                workspace=self.workspace,
                started_at=datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
                skill_version=VERSION,
                skill_version_source="TEST",
                source_root=ROOT,
                adapter_root=ADAPTER_ROOT,
            )

        receipt_path = self.last_receipt_path()
        receipt = load_env(receipt_path)
        self.assertEqual(result["REMOTE"], "ALIGNED")
        self.assertEqual(result["WRITE_GATE"], "PASS")
        self.assertTrue(verify_receipt(receipt_path))
        self.assertEqual(receipt["REMOTE_REF"], "refs/heads/main")
        self.assertEqual(receipt["REMOTE_QUERY_ATTEMPTED"], "TRUE")
        self.assertEqual(
            receipt["REMOTE_QUERY_CONFIRMED_SOURCE_ID"],
            pending.source_id,
        )
