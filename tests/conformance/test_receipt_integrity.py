from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from support import AdapterHarness
from sextante.envfile import canonical_env, load_env
from sextante.receipt import verify_receipt, write_receipt


class ReceiptIntegrityTests(AdapterHarness):
    def write_rehashed(self, values: dict[str, str], name: str):
        forged_values = dict(values)
        forged_values.pop("RECEIPT_HASH", None)
        forged_values["RECEIPT_ID"] = f"sextante-{name}"
        payload = canonical_env(forged_values)
        forged_values["RECEIPT_HASH"] = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()
        path = self.base / f"{name}.env"
        path.write_bytes(canonical_env(forged_values).encode("utf-8"))
        return path

    def test_hash_only_forgery_is_rejected(self) -> None:
        forged = self.base / "forged.env"
        values = {"WRITE_GATE": "PASS"}
        digest = hashlib.sha256(canonical_env(values).encode("utf-8")).hexdigest()
        values["RECEIPT_HASH"] = digest
        forged.write_text(canonical_env(values), encoding="utf-8")

        self.assertFalse(verify_receipt(forged))

    def test_invalid_normalized_value_with_valid_hash_is_rejected(self) -> None:
        self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|shell|INVOKABLE|UNKNOWN",
        )
        values = load_env(self.last_receipt_path())
        values.pop("RECEIPT_HASH")
        values["RECEIPT_ID"] = "sextante-invalid-enum"
        values["LOCAL"] = "MAYBE"
        payload = canonical_env(values)
        values["RECEIPT_HASH"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        invalid_path = self.base / "invalid-enum.env"
        invalid_path.write_text(canonical_env(values), encoding="utf-8")

        self.assertFalse(verify_receipt(invalid_path))

    def test_rehashed_unknown_capability_cannot_claim_aligned(self) -> None:
        _, values = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|shell|INVOKABLE|UNKNOWN",
            "--intent",
            "edit",
            "--target-where",
            "local:workspace",
            "--target-action",
            "EDIT",
            "--target-confirmed-by",
            "human:owner",
        )
        values["CAPABILITY_001"] = "tool|shell|UNKNOWN|1"
        values["CAPABILITIES_HASH"] = hashlib.sha256(
            values["CAPABILITY_001"].encode("utf-8")
        ).hexdigest()

        forged = self.write_rehashed(values, "forged-capability")

        self.assertEqual(values["WRITE_GATE"], "PASS")
        self.assertFalse(verify_receipt(forged))

    def test_rehashed_unknown_runtime_cannot_claim_aligned(self) -> None:
        _, values = self.run_adapter(
            "--runtime-result",
            "ALIGNED",
            "--runtime-version",
            "build-1",
            "--runtime-target",
            "runtime:dev",
            "--runtime-source",
            "harness:runtime-probe",
            "--runtime-evidence",
            "VERIFIED_DIRECT",
            "--capability",
            "tool|deploy|INVOKABLE|UNKNOWN",
            "--intent",
            "deploy",
            "--target-where",
            "runtime:dev",
            "--target-action",
            "DEPLOY",
            "--target-confirmed-by",
            "human:owner",
        )
        values["RUNTIME_TARGET"] = "UNKNOWN"
        values["RUNTIME_EVIDENCE_LEVEL"] = "UNKNOWN"
        values["TARGET_WHERE"] = "UNKNOWN"

        forged = self.write_rehashed(values, "forged-runtime")

        self.assertEqual(values["WRITE_GATE"], "PASS")
        self.assertFalse(verify_receipt(forged))

    def test_rehashed_no_remote_cannot_claim_aligned(self) -> None:
        _, values = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|shell|INVOKABLE|UNKNOWN",
            "--intent",
            "edit",
            "--target-where",
            "local:workspace",
            "--target-action",
            "EDIT",
            "--target-confirmed-by",
            "human:owner",
        )
        values["REMOTE"] = "ALIGNED"

        forged = self.write_rehashed(values, "forged-remote-state")

        self.assertEqual(values["REMOTE_STATE"], "NO_GIT")
        self.assertEqual(values["WRITE_GATE"], "PASS")
        self.assertFalse(verify_receipt(forged))

    def test_rehashed_local_source_mismatch_is_rejected(self) -> None:
        self.init_committed_repository()
        _, values = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|git|INVOKABLE|UNKNOWN",
            "--intent",
            "edit",
            "--target-where",
            "local:workspace",
            "--target-action",
            "EDIT",
            "--target-confirmed-by",
            "human:owner",
        )
        values["LOCAL_SOURCE"] = "WORKSPACE_METADATA"

        forged = self.write_rehashed(values, "forged-local-source")

        self.assertEqual(values["WRITE_GATE"], "PASS")
        self.assertFalse(verify_receipt(forged))

    def test_remote_source_id_is_recomputed(self) -> None:
        self.init_committed_repository()
        self.git("remote", "add", "origin", "https://example.com/repository.git")
        _, values = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|git|INVOKABLE|UNKNOWN",
        )
        self.assertEqual(values["REMOTE_STATE"], "NETWORK_CONFIRMATION_REQUIRED")
        values["REMOTE_SOURCE_ID"] = f"sha256:{'0' * 64}"

        forged = self.write_rehashed(values, "forged-remote-source")

        self.assertFalse(verify_receipt(forged))

    def test_concurrent_writers_cannot_replace_immutable_receipt(self) -> None:
        self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|shell|INVOKABLE|UNKNOWN",
        )
        values = load_env(self.last_receipt_path())
        values.pop("RECEIPT_HASH")
        values["RECEIPT_ID"] = "sextante-concurrency-fixture"
        race_root = self.base / "race-receipts"
        barrier = Barrier(8)

        def attempt_write() -> bool:
            barrier.wait()
            try:
                write_receipt(
                    values,
                    workspace=self.workspace,
                    receipt_root=race_root,
                )
            except ValueError:
                return False
            return True

        with ThreadPoolExecutor(max_workers=8) as executor:
            outcomes = tuple(executor.map(lambda _: attempt_write(), range(8)))

        self.assertEqual(sum(outcomes), 1)
        receipt = self.last_receipt_path(race_root)
        self.assertTrue(verify_receipt(receipt))
        self.assertFalse(tuple(receipt.parent.glob("*.tmp")))
