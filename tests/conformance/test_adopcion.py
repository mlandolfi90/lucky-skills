from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from support import ADAPTER_ROOT, ROOT

sys.path.insert(0, str(ADAPTER_ROOT))

from adopcion.planner import build_plan  # noqa: E402
from adopcion.transaction import apply_plan, revalidate_state_map  # noqa: E402
from lifecycle_core.envfile import canonical_env, load_env  # noqa: E402
from lifecycle_core.hashing import tree_hash  # noqa: E402
from lifecycle_core.receipts import verify_receipt  # noqa: E402
from sextante.local_probe import probe_local  # noqa: E402


class AdoptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.catalog = self.base / "catalog" / "skills"
        self.target = self.base / "target"
        self.receipts = self.base / "sextante-receipts"
        self.catalog.mkdir(parents=True)
        self.target.mkdir()
        self.skill = self._write_skill("alpha")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_adopts_and_is_idempotent(self) -> None:
        landing = self._landing()
        plan = self._plan(landing)
        receipt = apply_plan(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:test",
        )

        self.assertTrue(verify_receipt(receipt))
        self.assertTrue((self.target / "skills" / "alpha" / "SKILL.md").is_file())
        self.assertTrue(
            (self.target / ".agents" / "skills" / "alpha" / "SKILL.md").is_file()
        )
        state = load_env(self.target / ".lifecycle" / "state" / "skills" / "alpha.env")
        self.assertEqual(state["SKILL_VERSION"], "1.0.0")
        self.assertEqual(
            (self.target / ".lifecycle" / ".gitignore").read_text(encoding="utf-8"),
            "local/\n",
        )
        self.assertEqual(
            (self.target / ".lifecycle" / ".gitattributes").read_text(encoding="utf-8"),
            "* text=auto eol=lf\n",
        )

        second = self._plan(self._landing())
        self.assertFalse(second.has_writes)
        second_receipt = apply_plan(
            second,
            confirmed_plan_hash=second.plan_hash,
            confirmed_by="human:test",
        )
        self.assertEqual(load_env(second_receipt)["RESULT"], "ALREADY_ADOPTED")

    def test_state_source_is_portable_and_free_of_local_paths(self) -> None:
        plan = self._plan(self._landing())
        apply_plan(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:test",
        )

        state = load_env(self.target / ".lifecycle" / "state" / "skills" / "alpha.env")
        # El estado adoptado se versiona y se pushea a cada destino (D-058);
        # una ruta absoluta filtra el usuario local y hace que dos máquinas
        # escriban estados distintos para la misma versión.
        self.assertEqual(state["SOURCE"], "skills/alpha")
        raw = (
            self.target / ".lifecycle" / "state" / "skills" / "alpha.env"
        ).read_text(encoding="utf-8")
        self.assertNotIn(str(self.base), raw)

    def test_plan_enumerates_files_removed_by_archive_replace(self) -> None:
        old = self.target / "skills" / "alpha"
        (old / "data").mkdir(parents=True)
        (old / "SKILL.md").write_text("# distinto\n", encoding="utf-8")
        (old / "NOTAS-PROPIAS.md").write_text("mías\n", encoding="utf-8")
        (old / "data" / "config.json").write_text("{}\n", encoding="utf-8")

        plan = self._plan(self._landing())

        canonical = next(
            item
            for item in plan.items
            if item.role == "CANONICAL" and item.skill_id == "alpha"
        )
        self.assertEqual(canonical.action, "ARCHIVE_REPLACE")
        # Las bajas quedan dentro del plan (y por lo tanto del PLAN_HASH que el
        # humano confirma): sin esto la compuerta mostraba menos de lo que la
        # operación hacía (D-041, D-052).
        self.assertEqual(
            canonical.removes,
            ("NOTAS-PROPIAS.md", "data/config.json"),
        )
        self.assertIn("removes", plan.to_dict()["items"][0])

    def test_update_over_adopted_repo_regenerates_state_map(self) -> None:
        # El ciclo de actualización: adoptar, cambiar la skill en el catálogo y
        # volver a adoptar. Con la huella pre-instalación coincidiendo con el
        # STATE-MAP (caso normal desde V4), el planner lo marcaba `UNCHANGED`,
        # la instalación cambiaba el árbol, y la validación final rechazaba con
        # "STATE-MAP no coincide con el TARGET".
        first = self._plan(self._landing())
        apply_plan(
            first,
            confirmed_plan_hash=first.plan_hash,
            confirmed_by="human:test",
        )

        (self.skill / "SKILL.md").write_text(
            (
                "---\n"
                "name: alpha\n"
                "description: Skill de prueba portable.\n"
                "---\n\n"
                "# alpha v2\n"
            ),
            encoding="utf-8",
        )
        update = self._plan(self._landing())

        state_map = next(item for item in update.items if item.role == "STATE_MAP")
        self.assertEqual(state_map.action, "ARCHIVE_REPLACE")

        receipt = apply_plan(
            update,
            confirmed_plan_hash=update.plan_hash,
            confirmed_by="human:test",
        )
        self.assertTrue(verify_receipt(receipt))
        installed = (self.target / "skills" / "alpha" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("# alpha v2", installed)

    def test_receipt_declares_vcs_visibility_when_gitignore_swallows(self) -> None:
        # Un .gitignore anti-secretos (*.env, state/) puede tragarse los
        # metadatos de gobernanza en silencio; la adopción debe declararlo.
        subprocess.run(["git", "init", "-q", str(self.target)], check=True)
        subprocess.run(["git", "-C", str(self.target), "config",
                        "user.email", "t@t"], check=True)
        subprocess.run(["git", "-C", str(self.target), "config",
                        "user.name", "t"], check=True)
        (self.target / ".gitignore").write_text(
            "*.env\nstate/\n", encoding="utf-8"
        )
        plan = self._plan(self._landing())
        receipt = apply_plan(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:test",
        )
        values = load_env(receipt)
        visible, total = values["VCS_VISIBLE"].split("/")
        self.assertLess(int(visible), int(total))
        self.assertIn(".lifecycle/state/STATE-MAP.env", values["VCS_IGNORED"])

    def test_revalidar_unblocks_a_repo_that_advanced_after_adoption(self) -> None:
        # El deadlock de la flota: adoptar, commitear, seguir trabajando
        # (contenido nuevo), y toda adopción posterior bloqueada por drift
        # honesto — sin vía de re-corroboración. revalidar es esa vía.
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.target)],
                       check=True)
        for key, value in (("user.email", "t@t"), ("user.name", "t")):
            subprocess.run(["git", "-C", str(self.target), "config", key, value],
                           check=True)
        plan = self._plan(self._landing())
        apply_plan(plan, confirmed_plan_hash=plan.plan_hash,
                   confirmed_by="human:test")
        subprocess.run(["git", "-C", str(self.target), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.target), "commit", "-qm",
                        "adopta gobernanza"], check=True)
        # El repo vive: contenido nuevo commiteado después de adoptar.
        (self.target / "app.py").write_text("codigo\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.target), "add", "app.py"],
                       check=True)
        subprocess.run(["git", "-C", str(self.target), "commit", "-qm",
                        "trabajo del proyecto"], check=True)

        with self.assertRaisesRegex(ValueError, "WRITE_GATE|edición"):
            self._plan(self._landing())

        receipt = revalidate_state_map(self.target, confirmed_by="human:test")
        values = load_env(receipt)
        self.assertEqual(values["OPERATION"], "REVALIDATE")
        self.assertNotEqual(values["PREVIOUS_FINGERPRINT"],
                            values["NEW_FINGERPRINT"])

        second = self._plan(self._landing())
        # El STATE-MAP revalidado (modificado sin commitear, con recibo) no es
        # trabajo ajeno: no debe aparecer como colisión del plan siguiente.
        self.assertEqual(second.collisions, ())
        result = apply_plan(second, confirmed_plan_hash=second.plan_hash,
                            confirmed_by="human:test")
        self.assertTrue(verify_receipt(result))

    def test_revalidar_requires_an_adopted_repo(self) -> None:
        with self.assertRaisesRegex(ValueError, "no está adoptado"):
            revalidate_state_map(self.target, confirmed_by="human:test")

    def test_archives_replaced_and_legacy_paths(self) -> None:
        old = self.target / "skills" / "alpha"
        old.mkdir(parents=True)
        (old / "old.txt").write_text("old\n", encoding="utf-8")
        legacy = self.target / "skills" / "lifecycle" / "gobernanza"
        legacy.mkdir(parents=True)
        (legacy / "rule.md").write_text("legacy\n", encoding="utf-8")

        plan = self._plan(
            self._landing(),
            legacy_paths=("skills/lifecycle/gobernanza",),
        )
        receipt = apply_plan(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:test",
        )
        archive = self.target / ".lifecycle" / "archive" / plan.adoption_id
        self.assertTrue((archive / "files" / "skills" / "alpha" / "old.txt").is_file())
        self.assertTrue(
            (
                archive / "files" / "skills" / "lifecycle" / "gobernanza" / "rule.md"
            ).is_file()
        )
        self.assertFalse(legacy.exists())
        self.assertTrue(verify_receipt(receipt))

    def test_legacy_path_can_contain_spaces_and_unicode(self) -> None:
        legacy = self.target / "skills" / "viejo módulo"
        legacy.mkdir(parents=True)
        (legacy / "regla vieja.md").write_text("legacy\n", encoding="utf-8")
        plan = self._plan(
            self._landing(),
            legacy_paths=("skills/viejo módulo",),
        )
        apply_plan(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:test",
        )
        archived = (
            self.target
            / ".lifecycle"
            / "archive"
            / plan.adoption_id
            / "files"
            / "skills"
            / "viejo módulo"
            / "regla vieja.md"
        )
        self.assertTrue(archived.is_file())
        self.assertFalse(legacy.exists())

    def test_sensitive_archive_requires_human_and_stays_local(self) -> None:
        old = self.target / "skills" / "alpha"
        old.mkdir(parents=True)
        (old / "secret.key").write_text("not-a-real-secret\n", encoding="utf-8")
        plan = self._plan(self._landing())
        self.assertTrue(plan.risks)

        with self.assertRaisesRegex(ValueError, "human:"):
            apply_plan(
                plan,
                confirmed_plan_hash=plan.plan_hash,
                confirmed_by="human:test",
            )

        apply_plan(
            plan,
            confirmed_plan_hash=plan.plan_hash,
            confirmed_by="human:test",
            accept_risk_by="human:test",
        )
        local_payload = (
            self.target
            / ".lifecycle"
            / "local"
            / "archive"
            / plan.adoption_id
            / "files"
            / "skills"
            / "alpha"
            / "secret.key"
        )
        versioned_manifest = (
            self.target / ".lifecycle" / "archive" / plan.adoption_id / "MANIFEST.env"
        )
        self.assertTrue(local_payload.is_file())
        self.assertFalse(
            (
                versioned_manifest.parent / "files" / "skills" / "alpha" / "secret.key"
            ).exists()
        )
        self.assertIn(
            ".lifecycle/local/archive/",
            load_env(versioned_manifest)["PAYLOAD_LOCATION"],
        )

    def test_stale_landing_blocks_replan(self) -> None:
        landing = self._landing()
        (self.target / "changed.txt").write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "stale"):
            self._plan(landing)

    def test_apply_revalidates_plan_even_through_direct_api(self) -> None:
        plan = self._plan(self._landing())
        (self.target / "changed.txt").write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "stale|estado cambió"):
            apply_plan(
                plan,
                confirmed_plan_hash=plan.plan_hash,
                confirmed_by="human:test",
            )

    def test_preexisting_local_archive_survives_failed_apply(self) -> None:
        initial = self._plan(self._landing())
        apply_plan(
            initial,
            confirmed_plan_hash=initial.plan_hash,
            confirmed_by="human:test",
        )
        installed = self.target / "skills" / "alpha"
        (installed / "secret.key").write_text(
            "not-a-real-secret\n",
            encoding="utf-8",
        )
        self._corroborate_state_map()
        plan = self._plan(self._landing())
        self.assertTrue(plan.risks)
        existing = (
            self.target
            / ".lifecycle"
            / "local"
            / "archive"
            / plan.adoption_id
            / "files"
        )
        existing.mkdir(parents=True)
        canary = existing / "CANARY.txt"
        canary.write_text("keep\n", encoding="utf-8")
        before = tree_hash(installed)

        with self.assertRaisesRegex(ValueError, "archivo local"):
            apply_plan(
                plan,
                confirmed_plan_hash=plan.plan_hash,
                confirmed_by="human:test",
                accept_risk_by="human:test",
            )

        self.assertEqual(canary.read_text(encoding="utf-8"), "keep\n")
        self.assertEqual(tree_hash(installed), before)

    def test_preexisting_archive_sibling_survives_rollback(self) -> None:
        initial = self._plan(self._landing())
        apply_plan(
            initial,
            confirmed_plan_hash=initial.plan_hash,
            confirmed_by="human:test",
        )
        installed = self.target / "skills" / "alpha"
        (installed / "secret.key").write_text(
            "not-a-real-secret\n",
            encoding="utf-8",
        )
        self._corroborate_state_map()
        plan = self._plan(self._landing())
        adoption_root = (
            self.target / ".lifecycle" / "local" / "archive" / plan.adoption_id
        )
        adoption_root.mkdir(parents=True)
        canary = adoption_root / "CANARY.txt"
        canary.write_text("keep\n", encoding="utf-8")

        with (
            patch(
                "adopcion.transaction._validate_activation",
                side_effect=ValueError("fixture failure"),
            ),
            self.assertRaisesRegex(ValueError, "fixture failure"),
        ):
            apply_plan(
                plan,
                confirmed_plan_hash=plan.plan_hash,
                confirmed_by="human:test",
                accept_risk_by="human:test",
            )

        self.assertEqual(canary.read_text(encoding="utf-8"), "keep\n")
        self.assertFalse((adoption_root / "files").exists())

    def test_receipt_failure_rolls_back_the_whole_adoption(self) -> None:
        plan = self._plan(self._landing())

        with (
            patch(
                "adopcion.transaction.write_receipt",
                side_effect=OSError("fixture receipt failure"),
            ),
            self.assertRaisesRegex(OSError, "fixture receipt failure"),
        ):
            apply_plan(
                plan,
                confirmed_plan_hash=plan.plan_hash,
                confirmed_by="human:test",
            )

        self.assertFalse((self.target / "skills").exists())
        self.assertFalse((self.target / ".agents").exists())
        self.assertFalse((self.target / ".lifecycle").exists())

    def test_commit_request_on_non_git_target_fails_before_writing(self) -> None:
        plan = self._plan(self._landing())

        with self.assertRaisesRegex(ValueError, "no usa Git"):
            apply_plan(
                plan,
                confirmed_plan_hash=plan.plan_hash,
                confirmed_by="human:test",
                create_commit=True,
                commit_confirmed_by="human:test",
            )

        self.assertFalse((self.target / "skills").exists())
        self.assertFalse((self.target / ".agents").exists())
        self.assertFalse((self.target / ".lifecycle").exists())

    def test_validation_failure_restores_previous_state(self) -> None:
        old = self.target / "skills" / "alpha"
        old.mkdir(parents=True)
        (old / "old.txt").write_text("old\n", encoding="utf-8")
        plan = self._plan(self._landing())

        with patch(
            "adopcion.transaction._validate_activation",
            side_effect=ValueError("fixture failure"),
        ):
            with self.assertRaisesRegex(ValueError, "fixture failure") as raised:
                apply_plan(
                    plan,
                    confirmed_plan_hash=plan.plan_hash,
                    confirmed_by="human:test",
                )

        self.assertEqual(
            (self.target / "skills" / "alpha" / "old.txt").read_text(encoding="utf-8"),
            "old\n",
        )
        self.assertFalse((self.target / ".agents").exists())
        self.assertFalse((self.target / ".lifecycle").exists())
        # La excepción confirma el rollback sin cambiar su tipo ni su mensaje.
        self.assertIn(
            "ROLLBACK=RESTORED",
            "".join(getattr(raised.exception, "__notes__", [])),
        )

    def test_plan_hash_must_match_confirmation(self) -> None:
        plan = self._plan(self._landing())
        with self.assertRaisesRegex(ValueError, "PLAN_HASH"):
            apply_plan(
                plan,
                confirmed_plan_hash="0" * 64,
                confirmed_by="human:test",
            )

    def _plan(
        self,
        landing: Path,
        *,
        legacy_paths: tuple[str, ...] = (),
    ):
        return build_plan(
            source_skill=self.skill,
            target=self.target,
            harness="codex",
            landing_receipt=landing,
            legacy_paths=legacy_paths,
        )

    def _write_skill(self, name: str) -> Path:
        root = self.catalog / name
        root.mkdir()
        (root / "SKILL.md").write_text(
            (
                "---\n"
                f"name: {name}\n"
                "description: Skill de prueba portable.\n"
                "---\n\n"
                f"# {name}\n"
            ),
            encoding="utf-8",
        )
        (root / "manifest.env").write_text(
            (
                'FORMAT_VERSION="1"\n'
                f'SKILL_ID="{name}"\n'
                'SKILL_VERSION="1.0.0"\n'
                'REQUIRES=""\n'
            ),
            encoding="utf-8",
        )
        (root / ".gitattributes").write_text(
            "* text=auto eol=lf\n",
            encoding="utf-8",
            newline="\n",
        )
        return root

    def _landing(self) -> Path:
        before = set(self.receipts.rglob("sextante-*.env"))
        command = [
            sys.executable,
            "-B",
            str(ADAPTER_ROOT / "run_sextante.py"),
            "--workspace",
            str(self.target),
            "--source-root",
            str(ROOT),
            "--harness",
            "codex",
            "--execution-level",
            "NATIVE",
            "--runtime-result",
            "NOT_APPLICABLE",
            "--runtime-source",
            "fixture:no-runtime",
            "--runtime-evidence",
            "VERIFIED_DIRECT",
            "--capability",
            "harness|codex|INVOKABLE",
            "--capabilities-evidence",
            "VERIFIED_DIRECT",
            "--readme-policy",
            "IGNORE",
            "--intent",
            "edit",
            "--target-where",
            "local:workspace",
            "--target-action",
            "EDIT",
            "--target-confirmed-by",
            "human:test",
            "--receipt-root",
            str(self.receipts),
            "--collected-by",
            "session:mother:test",
            "--synthesized-by",
            "session:mother:test",
            "--decided-by",
            "human:test",
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        created = set(self.receipts.rglob("sextante-*.env")) - before
        self.assertEqual(len(created), 1)
        return created.pop()

    def _corroborate_state_map(self) -> None:
        path = self.target / ".lifecycle" / "state" / "STATE-MAP.env"
        values = load_env(path)
        observation, _ = probe_local(
            self.target,
            timeout_seconds=10,
            max_entries=50_000,
        )
        values["GIT_LOCAL_FINGERPRINT"] = observation.fingerprint
        path.write_text(
            canonical_env(values),
            encoding="utf-8",
            newline="\n",
        )
        corroborated, _ = probe_local(
            self.target,
            timeout_seconds=10,
            max_entries=50_000,
        )
        self.assertEqual(corroborated.fingerprint, observation.fingerprint)


if __name__ == "__main__":
    unittest.main()
