from __future__ import annotations

import ast
from pathlib import Path

from clinicdesk.app.common.politica_saneo_auditoria_telemetria import (
    CLAVES_CONTEXTO_TELEMETRIA_PERMITIDAS,
    CLAVES_METADATA_AUDITORIA_PERMITIDAS,
)

RUTA_USECASE_AUDITORIA = Path("clinicdesk/app/application/usecases/registrar_auditoria_acceso.py")
RUTA_USECASE_TELEMETRIA = Path("clinicdesk/app/application/usecases/registrar_telemetria.py")
RUTA_PERSISTENCIA = Path("clinicdesk/app/infrastructure/sqlite/persistencia_segura_auditoria_telemetria.py")


def _nombres_usados_en_modulo(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    return {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)}


def test_allowlists_oficiales_tienen_contrato_explicito_esperado() -> None:
    assert CLAVES_METADATA_AUDITORIA_PERMITIDAS == {
        "origen",
        "modulo",
        "vista",
        "accion_ui",
        "reason_code",
        "duracion_ms",
        "resultado",
        "contexto",
    }
    assert CLAVES_CONTEXTO_TELEMETRIA_PERMITIDAS == {
        "page",
        "origen",
        "tipo",
        "clave",
        "resultado",
        "destino",
        "vista",
        "found",
        "modulo",
        "accion_ui",
        "reason_code",
        "contexto",
        "tab",
        "detalle",
    }


def test_usecases_y_persistencia_reusan_allowlists_oficiales() -> None:
    nombres_auditoria = _nombres_usados_en_modulo(RUTA_USECASE_AUDITORIA)
    nombres_telemetria = _nombres_usados_en_modulo(RUTA_USECASE_TELEMETRIA)
    nombres_persistencia = _nombres_usados_en_modulo(RUTA_PERSISTENCIA)

    assert "CLAVES_METADATA_AUDITORIA_PERMITIDAS" in nombres_auditoria
    assert "CLAVES_CONTEXTO_TELEMETRIA_PERMITIDAS" in nombres_telemetria
    assert "CLAVES_METADATA_AUDITORIA_PERMITIDAS" in nombres_persistencia
    assert "CLAVES_CONTEXTO_TELEMETRIA_PERMITIDAS" in nombres_persistencia
