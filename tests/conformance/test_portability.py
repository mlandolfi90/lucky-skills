from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from unittest.mock import patch

from support import (
    ADAPTER_ROOT,
    ROOT,
    VERSION,
    AdapterHarness,
    parse_visible_summary,
    run_adapter_process,
)
from sextante import cli
from sextante.component_contracts import (
    POLICY_DEFAULTS,
    POLICY_LIMITS,
    valid_policy,
    valid_sources,
    valid_state_map,
)
from sextante.envfile import canonical_env, load_env, load_env_document
from sextante.fingerprint_contract import canonical_record, fingerprint_records
from sextante.identity import adapter_fingerprint, resolve_source_identity
from sextante.local_fingerprint_policy import (
    git_blob_oids,
    normalize_fingerprint_material,
)
from sextante.local_probe import probe_local
from sextante.project_config import load_project_config
from sextante.receipt import verify_receipt


class PortabilityTests(AdapterHarness):
    def test_lifecycle_templates_are_canonical_and_valid(self) -> None:
        templates = (
            ("config/SEXTANTE.env", valid_policy),
            ("config/SOURCES.env", valid_sources),
            ("state/STATE-MAP.env", valid_state_map),
        )
        for relative_path, validator in templates:
            with self.subTest(template=relative_path):
                raw, values = load_env_document(
                    ROOT / "templates" / "lifecycle" / relative_path
                )
                self.assertEqual(raw, canonical_env(values))
                self.assertTrue(validator(values))

    def test_standalone_skill_vectors_match_reference_adapter(self) -> None:
        copied = self.base / "standalone-skill-vectors"
        shutil.copytree(ROOT / "skills" / "sextante", copied)
        vectors = json.loads(
            (copied / "references" / "conformance-v1.json").read_text(encoding="utf-8")
        )

        self.assertEqual(vectors["policy_defaults"], POLICY_DEFAULTS)
        self.assertEqual(vectors["policy_limits"], POLICY_LIMITS)

        status_fields = {
            "POLICY": "policy_status",
            "SOURCES": "sources_status",
            "STATE_MAP": "state_map_status",
        }
        for case in vectors["component_cases"]:
            with self.subTest(case=case["id"]):
                workspace = self.base / "component-cases" / case["id"]
                target = workspace / ".lifecycle" / case["relative_path"]
                target.parent.mkdir(parents=True)
                target.write_bytes(case["raw"].encode("utf-8"))
                project = load_project_config(workspace)
                actual = getattr(project, status_fields[case["component"]])
                self.assertEqual(actual, case["expected_status"])

        for case in vectors["record_cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(canonical_record(*case["fields"]), case["expected"])

        for case in vectors["fingerprint_cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    fingerprint_records(case["records"]),
                    case["sha256"],
                )

        for case in vectors["state_map_normalization_cases"]:
            with self.subTest(case=case["id"]):
                normalized, changed = normalize_fingerprint_material(
                    case["path"],
                    case["input"].encode("utf-8"),
                )
                self.assertEqual(normalized.decode("utf-8"), case["expected"])
                self.assertEqual(changed, case["changed"])
                self.assertEqual(
                    git_blob_oids(normalized),
                    (case["blob_sha1"], case["blob_sha256"]),
                )

        empty_vector = next(
            case
            for case in vectors["fingerprint_cases"]
            if case["id"] == "empty-unversioned-workspace"
        )
        observed, _ = probe_local(
            self.workspace,
            timeout_seconds=5,
            max_entries=100,
        )
        self.assertEqual(observed.fingerprint, empty_vector["sha256"])

    def test_skill_copy_has_no_required_reference_outside_its_package(self) -> None:
        copied = self.base / "standalone-skill"
        shutil.copytree(ROOT / "skills" / "sextante", copied)

        for document in copied.rglob("*.md"):
            content = document.read_text(encoding="utf-8")
            for reference in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
                if "://" in reference or reference.startswith("#"):
                    continue
                target = (document.parent / reference).resolve()
                self.assertTrue(target.is_relative_to(copied.resolve()))
                self.assertTrue(target.is_file(), f"referencia ausente: {reference}")

    def test_copied_adapter_runs_with_explicit_version(self) -> None:
        copied = self.base / "standalone-adapter"
        shutil.copytree(
            ADAPTER_ROOT,
            copied,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        standalone_receipts = self.base / "standalone-receipts"

        completed = run_adapter_process(
            script=copied / "run_sextante.py",
            workspace=self.workspace,
            receipt_root=standalone_receipts,
            extra_arguments=[
                "--skill-version",
                VERSION,
                "--runtime-result",
                "NOT_APPLICABLE",
                "--runtime-source",
                "fixture:no-runtime",
                "--runtime-evidence",
                "VERIFIED_DIRECT",
                "--capability",
                f"skill|sextante|LOADED|{VERSION}",
            ],
            cwd=self.base,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        summary = parse_visible_summary(completed.stdout)
        self.assertEqual(summary["LOCAL"], "ALIGNED")
        self.assertTrue(self.last_receipt_path(standalone_receipts).is_file())

    def test_copied_adapter_runs_with_explicit_source_root(self) -> None:
        copied = self.base / "source-root-adapter"
        shutil.copytree(
            ADAPTER_ROOT,
            copied,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        version_root = self.base / "version-root"
        version_root.mkdir()
        (version_root / "VERSION").write_text(f"{VERSION}\n", encoding="utf-8")
        receipts = self.base / "source-root-receipts"

        completed = run_adapter_process(
            script=copied / "run_sextante.py",
            workspace=self.workspace,
            receipt_root=receipts,
            extra_arguments=[
                "--source-root",
                str(version_root),
                "--runtime-result",
                "NOT_APPLICABLE",
                "--runtime-source",
                "fixture:no-runtime",
                "--runtime-evidence",
                "VERIFIED_DIRECT",
                "--capability",
                f"skill|sextante|LOADED|{VERSION}",
            ],
            cwd=self.base,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        parse_visible_summary(completed.stdout)

    def test_identity_autodiscovery_and_conflict_rules(self) -> None:
        bundle_root = self.base / "nested" / "bundle"
        copied = bundle_root / "adapters" / "reference_python"
        copied.parent.mkdir(parents=True)
        shutil.copytree(
            ADAPTER_ROOT,
            copied,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        (bundle_root / "VERSION").write_text(f"{VERSION}\n", encoding="utf-8")

        discovered = resolve_source_identity(
            explicit_version="",
            explicit_source_root="",
            adapter_root=copied,
        )
        self.assertEqual(discovered.source_root, bundle_root)
        self.assertEqual(discovered.version_source, "SOURCE_ROOT_DISCOVERED")
        with self.assertRaises(ValueError):
            resolve_source_identity(
                explicit_version="different",
                explicit_source_root=str(bundle_root),
                adapter_root=copied,
            )
        with self.assertRaises(ValueError):
            resolve_source_identity(
                explicit_version="",
                explicit_source_root="",
                adapter_root=self.base / "standalone-without-version",
            )

    def test_real_adapter_content_change_changes_inventory_hash(self) -> None:
        copied = self.base / "mutable-adapter"
        shutil.copytree(
            ADAPTER_ROOT,
            copied,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        before = adapter_fingerprint(copied)
        module = copied / "sextante" / "__init__.py"
        module.write_text(
            module.read_text(encoding="utf-8") + "\n# changed\n",
            encoding="utf-8",
        )

        self.assertNotEqual(before, adapter_fingerprint(copied))

    def test_adapter_mutation_during_check_marks_result_stale(self) -> None:
        arguments = cli._parser().parse_args(
            [
                "--workspace",
                str(self.workspace),
                "--receipt-root",
                str(self.receipt_root),
                "--runtime-result",
                "NOT_APPLICABLE",
                "--runtime-source",
                "fixture:no-runtime",
                "--runtime-evidence",
                "VERIFIED_DIRECT",
                "--capability",
                "tool|shell|INVOKABLE|UNKNOWN",
            ]
        )

        with patch(
            "sextante.runner.adapter_fingerprint",
            side_effect=["a" * 64, "b" * 64],
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

        self.assertEqual(result["STATE_VERDICT"], "STALE")
        self.assertEqual(result["WRITE_GATE"], "BLOCK")
        self.assertEqual(result["HUMAN_DECISION"], "STOP")
        receipt_path = self.last_receipt_path()
        receipt = load_env(receipt_path)
        self.assertTrue(verify_receipt(receipt_path))
        self.assertEqual(receipt["ADAPTER_FINGERPRINT_STARTED"], "a" * 64)
        self.assertEqual(receipt["ADAPTER_FINGERPRINT_FINISHED"], "b" * 64)
        self.assertEqual(receipt["ADAPTER_CHANGED_DURING_CHECK"], "TRUE")

    def test_unavailable_final_adapter_probe_still_emits_stale_receipt(self) -> None:
        arguments = cli._parser().parse_args(
            [
                "--workspace",
                str(self.workspace),
                "--receipt-root",
                str(self.receipt_root),
                "--runtime-result",
                "NOT_APPLICABLE",
                "--runtime-source",
                "fixture:no-runtime",
                "--runtime-evidence",
                "VERIFIED_DIRECT",
                "--capability",
                "tool|shell|INVOKABLE|UNKNOWN",
            ]
        )

        with patch(
            "sextante.runner.adapter_fingerprint",
            side_effect=["a" * 64, ValueError("final probe unavailable")],
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
        self.assertEqual(result["STATE_VERDICT"], "STALE")
        self.assertEqual(result["WRITE_GATE"], "BLOCK")
        self.assertTrue(verify_receipt(receipt_path))
        self.assertEqual(receipt["ADAPTER_FINGERPRINT_FINISHED"], "UNAVAILABLE")
        self.assertEqual(receipt["ADAPTER_FINAL_STATUS"], "UNAVAILABLE")
        self.assertEqual(receipt["ADAPTER_CHANGED_DURING_CHECK"], "TRUE")
