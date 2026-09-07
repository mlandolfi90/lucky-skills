"""El kit corre contra el anfitrion de mentira. Si se rompe, se rompe aca."""

from conftest import CONFIG

from lucky_auditoria import Auditor
from lucky_auditoria.pruebas import KitDeAuditoria


class TestKitSobreUnAnfitrionDeMentira(KitDeAuditoria):
    herramienta_normal = "proyecto"
    argumento_no_declarado = "descripcion"

    def construir(self, tmp_path):
        config = tmp_path / "auditoria.toml"
        config.write_text(CONFIG, encoding="utf-8")
        return Auditor("mcp-de-prueba", config=config, version="0.0.1")
