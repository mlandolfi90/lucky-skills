from __future__ import annotations

from support import AdapterHarness, state_map_fixture, write_utf8_lf


class StateGateTests(AdapterHarness):
    def test_declared_no_runtime_remains_partial_until_corroborated(self) -> None:
        lifecycle = self.workspace / ".lifecycle"
        (lifecycle / "config").mkdir(parents=True)
        (lifecycle / "state").mkdir(parents=True)
        write_utf8_lf(
            lifecycle / "config" / "SOURCES.env",
            'REMOTE_NAME="AUTO"\n' 'RUNTIME_MODE="NONE"\n' 'RUNTIME_CANDIDATES=""\n',
        )
        write_utf8_lf(
            lifecycle / "state" / "STATE-MAP.env",
            state_map_fixture(local_commit="UNKNOWN"),
        )

        summary, receipt = self.run_adapter(
            "--capability",
            "tool|shell|INVOKABLE|UNKNOWN",
        )

        self.assertEqual(summary["RUNTIME"], "PARTIAL")
        self.assertEqual(summary["READ_GATE"], "WARN")
        self.assertEqual(receipt["RUNTIME_STATE"], "EVIDENCE_UNVERIFIED")
        self.assertEqual(receipt["RUNTIME_EVIDENCE_LEVEL"], "DECLARED")

    def test_noncanonical_state_map_is_invalid(self) -> None:
        lifecycle = self.workspace / ".lifecycle"
        (lifecycle / "state").mkdir(parents=True)
        noncanonical = state_map_fixture(local_commit="UNKNOWN").replace(
            'GIT_LOCAL_FINGERPRINT="UNKNOWN"',
            "GIT_LOCAL_FINGERPRINT=UNKNOWN",
        )
        write_utf8_lf(
            lifecycle / "state" / "STATE-MAP.env",
            noncanonical,
        )

        _, receipt = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|shell|INVOKABLE|UNKNOWN",
        )

        self.assertEqual(receipt["STATE_MAP_STATUS"], "INVALID")

    def test_state_map_expectations_do_not_turn_absence_into_drift(self) -> None:
        lifecycle = self.workspace / ".lifecycle"
        (lifecycle / "state").mkdir(parents=True)
        expected = (
            state_map_fixture(local_commit="UNKNOWN")
            .replace(
                'GIT_REMOTE_COMMIT="UNKNOWN"',
                f'GIT_REMOTE_COMMIT="{"a" * 40}"',
            )
            .replace(
                'GIT_REMOTE_REF="UNKNOWN"',
                'GIT_REMOTE_REF="refs/heads/main"',
            )
            .replace(
                'RUNTIME_VERSION="UNKNOWN"',
                'RUNTIME_VERSION="build-1"',
            )
            .replace(
                'CAPABILITIES_HASH="UNKNOWN"',
                f'CAPABILITIES_HASH="{"b" * 64}"',
            )
        )
        write_utf8_lf(
            lifecycle / "state" / "STATE-MAP.env",
            expected,
        )

        summary, receipt = self.run_adapter()

        self.assertEqual(receipt["STATE_MAP_STATUS"], "LOADED")
        self.assertEqual(summary["REMOTE"], "PARTIAL")
        self.assertEqual(summary["RUNTIME"], "PARTIAL")
        self.assertEqual(summary["CAPABILITIES"], "PARTIAL")
        self.assertNotIn("DRIFT", summary.values())

    def test_invalid_lifecycle_path_blocks_confirmed_edit(self) -> None:
        (self.workspace / ".lifecycle").write_text(
            "not-a-directory\n", encoding="utf-8"
        )

        summary, receipt = self.run_adapter(
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

        self.assertEqual(summary["WRITE_GATE"], "BLOCK")
        self.assertEqual(summary["HUMAN_DECISION"], "STOP")
        self.assertEqual(receipt["LIFECYCLE"], "INVALID")

    def test_project_file_cannot_bootstrap_readme_trust(self) -> None:
        self.init_committed_repository()
        current_commit = self.git("rev-parse", "HEAD").stdout.strip()
        lifecycle = self.workspace / ".lifecycle"
        (lifecycle / "config").mkdir(parents=True)
        (lifecycle / "state").mkdir(parents=True)
        (lifecycle / "config" / "SEXTANTE.env").write_text(
            'README_POLICY="DECLARED_TRUST"\n',
            encoding="utf-8",
        )
        write_utf8_lf(
            lifecycle / "state" / "STATE-MAP.env",
            state_map_fixture(local_commit=current_commit),
        )

        _, receipt = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|git|INVOKABLE|UNKNOWN",
        )

        self.assertEqual(receipt["README_POLICY"], "IGNORE")
        self.assertEqual(receipt["README_POLICY_CONFIRMED_BY"], "UNCONFIRMED")
        self.assertEqual(receipt["POLICY_STATUS"], "INVALID")

    def test_invalid_policy_does_not_erase_valid_drifting_state_map(self) -> None:
        self.init_committed_repository()
        lifecycle = self.workspace / ".lifecycle"
        (lifecycle / "config").mkdir(parents=True)
        (lifecycle / "state").mkdir(parents=True)
        (lifecycle / "config" / "SEXTANTE.env").write_text(
            'README_POLICY="IGNORE"\nREADME_POLICY="IGNORE"\n',
            encoding="utf-8",
        )
        write_utf8_lf(
            lifecycle / "state" / "STATE-MAP.env",
            state_map_fixture(local_commit="deadbeef"),
        )

        summary, receipt = self.run_adapter(
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

        self.assertEqual(summary["LOCAL"], "DRIFT")
        self.assertEqual(summary["WRITE_GATE"], "BLOCK")
        self.assertEqual(summary["HUMAN_DECISION"], "STOP")
        self.assertEqual(summary["DECISION_REASON"], "LOCAL_NOT_ALIGNED")
        self.assertEqual(receipt["POLICY_STATUS"], "INVALID")
        self.assertEqual(receipt["STATE_MAP_STATUS"], "LOADED")

    def test_invalid_config_blocks_even_when_local_state_map_matches(self) -> None:
        self.init_committed_repository()
        current_commit = self.git("rev-parse", "HEAD").stdout.strip()
        lifecycle = self.workspace / ".lifecycle"
        (lifecycle / "config").mkdir(parents=True)
        (lifecycle / "state").mkdir(parents=True)
        (lifecycle / "config" / "SEXTANTE.env").write_text(
            'README_POLICY="IGNORE"\nREADME_POLICY="IGNORE"\n',
            encoding="utf-8",
        )
        write_utf8_lf(
            lifecycle / "state" / "STATE-MAP.env",
            state_map_fixture(local_commit=current_commit),
        )

        summary, receipt = self.run_adapter(
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

        self.assertEqual(summary["LOCAL"], "ALIGNED")
        self.assertEqual(summary["WRITE_GATE"], "BLOCK")
        self.assertEqual(summary["HUMAN_DECISION"], "STOP")
        self.assertEqual(summary["DECISION_REASON"], "CONFIG_INVALID")
        self.assertEqual(receipt["CONFIG_STATUS"], "INVALID")

    def test_adopted_project_without_state_map_blocks_confirmed_edit(self) -> None:
        lifecycle = self.workspace / ".lifecycle"
        (lifecycle / "config").mkdir(parents=True)
        (lifecycle / "config" / "SEXTANTE.env").write_text(
            'README_POLICY="IGNORE"\n',
            encoding="utf-8",
        )

        summary, receipt = self.run_adapter(
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

        self.assertEqual(summary["WRITE_GATE"], "BLOCK")
        self.assertEqual(summary["HUMAN_DECISION"], "STOP")
        self.assertEqual(receipt["STATE_MAP_STATUS"], "ABSENT")

    def test_expired_runtime_evidence_blocks_deploy(self) -> None:
        summary, receipt = self.run_adapter(
            "--runtime-result",
            "ALIGNED",
            "--runtime-version",
            "build-1",
            "--runtime-target",
            "runtime:dev",
            "--runtime-source",
            "human:dev",
            "--runtime-evidence",
            "HUMAN_PROVIDED",
            "--runtime-observed-at",
            "2000-01-01T00:00:00Z",
            "--capability",
            "tool|shell|INVOKABLE|UNKNOWN",
            "--intent",
            "deploy",
            "--target-where",
            "runtime:dev",
            "--target-action",
            "DEPLOY",
            "--target-confirmed-by",
            "human:owner",
        )

        self.assertEqual(summary["RUNTIME"], "STALE")
        self.assertEqual(summary["STATE_VERDICT"], "STALE")
        self.assertEqual(summary["WRITE_GATE"], "BLOCK")
        self.assertEqual(receipt["RUNTIME_STATE"], "EVIDENCE_EXPIRED")

    def test_expired_capability_inventory_is_stale(self) -> None:
        summary, receipt = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|shell|INVOKABLE|UNKNOWN",
            "--capabilities-observed-at",
            "2000-01-01T00:00:00Z",
            "--intent",
            "edit",
            "--target-where",
            "local:workspace",
            "--target-action",
            "EDIT",
            "--target-confirmed-by",
            "human:owner",
        )

        self.assertEqual(summary["CAPABILITIES"], "STALE")
        self.assertEqual(summary["STATE_VERDICT"], "STALE")
        self.assertEqual(summary["WRITE_GATE"], "BLOCK")
        self.assertEqual(receipt["CAPABILITIES_STATE"], "EVIDENCE_EXPIRED")

    def test_unknown_capability_evidence_cannot_enable_edit(self) -> None:
        summary, receipt = self.run_adapter(
            "--runtime-result",
            "NOT_APPLICABLE",
            "--capability",
            "tool|shell|INVOKABLE|UNKNOWN",
            "--capabilities-evidence",
            "UNKNOWN",
            "--intent",
            "edit",
            "--target-where",
            "local:workspace",
            "--target-action",
            "EDIT",
            "--target-confirmed-by",
            "human:owner",
        )

        self.assertEqual(summary["CAPABILITIES"], "PARTIAL")
        self.assertEqual(summary["WRITE_GATE"], "BLOCK")
        self.assertEqual(summary["HUMAN_DECISION"], "STOP")
        self.assertEqual(
            summary["DECISION_REASON"],
            "CAPABILITIES_NOT_VERIFIED",
        )
        self.assertEqual(
            receipt["CAPABILITIES_STATE"],
            "EVIDENCE_UNVERIFIED",
        )

    def test_deploy_target_must_match_observed_runtime(self) -> None:
        summary, receipt = self.run_adapter(
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
            "runtime:prod",
            "--target-action",
            "DEPLOY",
            "--target-confirmed-by",
            "human:owner",
        )

        self.assertEqual(summary["WRITE_GATE"], "BLOCK")
        self.assertEqual(summary["HUMAN_DECISION"], "CONFIRM_TARGET")
        self.assertEqual(summary["DECISION_REASON"], "TARGET_WHERE_MISMATCH")
        self.assertEqual(receipt["RUNTIME_TARGET"], "runtime:dev")

    def test_matching_observed_runtime_can_enable_deploy(self) -> None:
        summary, _ = self.run_adapter(
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

        self.assertEqual(summary["WRITE_GATE"], "PASS")
