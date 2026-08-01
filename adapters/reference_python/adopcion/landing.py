from __future__ import annotations

from pathlib import Path

from lifecycle_core.envfile import load_env
from sextante.identity import adapter_fingerprint
from sextante.local_probe import probe_local
from sextante.project_config import load_project_config
from sextante.receipt import verify_receipt


def validate_landing(receipt_path: Path, target: Path) -> dict[str, str]:
    receipt = receipt_path.resolve(strict=True)
    if not verify_receipt(receipt):
        raise ValueError("comprobante de Sextante inválido")
    values = load_env(receipt)
    expected = {
        "WRITE_GATE": "PASS",
        "TARGET": "CONFIRMED",
        "TARGET_WHERE": "local:workspace",
        "TARGET_ACTION": "EDIT",
    }
    for key, value in expected.items():
        if values.get(key) != value:
            raise ValueError(f"Sextante no habilita edición: {key}")
    workspace = Path(values.get("WORKSPACE_PATH", "")).resolve(strict=True)
    target_resolved = target.resolve(strict=True)
    if workspace != target_resolved:
        raise ValueError("el workspace de Sextante no coincide con TARGET")
    project = load_project_config(target_resolved)
    current_contract = {
        "LIFECYCLE": project.lifecycle_status,
        "CONFIG_STATUS": project.status,
        "POLICY_STATUS": project.policy_status,
        "SOURCES_STATUS": project.sources_status,
        "STATE_MAP_STATUS": project.state_map_status,
    }
    for key, value in current_contract.items():
        if values.get(key) != value:
            raise ValueError(f"comprobante de Sextante stale: {key}")
    if not project.baseline_ready or project.status != "VALID":
        raise ValueError("Sextante ya no habilita el baseline del TARGET")
    observation, _ = probe_local(
        target_resolved,
        timeout_seconds=10,
        max_entries=50_000,
    )
    if observation.fingerprint != values.get("LOCAL_FINGERPRINT_FINISHED"):
        raise ValueError("comprobante de Sextante stale; revalidar TARGET")
    _validate_state_map(project.state_map, observation.fingerprint, observation.head)
    adapter_root = Path(__file__).resolve().parents[1]
    if adapter_fingerprint(adapter_root) != values.get("ADAPTER_FINGERPRINT_FINISHED"):
        raise ValueError("comprobante de Sextante stale: ADAPTER_FINGERPRINT")
    return values


def _validate_state_map(
    state_map: dict[str, str],
    fingerprint: str,
    commit: str,
) -> None:
    unknown = {"", "UNKNOWN", "N/D", "NOT_APPLICABLE"}
    expected_fingerprint = state_map.get("GIT_LOCAL_FINGERPRINT", "UNKNOWN")
    if expected_fingerprint not in unknown:
        if expected_fingerprint != fingerprint:
            raise ValueError("STATE-MAP ya no corrobora la huella local")
        return
    expected_commit = state_map.get("GIT_LOCAL_COMMIT", "UNKNOWN")
    if expected_commit not in unknown and expected_commit != commit:
        raise ValueError("STATE-MAP ya no corrobora el commit local")
