from __future__ import annotations

import re
from pathlib import Path

BASE_APP = Path("clinicdesk/app")
RUTAS_SELECT_PERMITIDAS = {
    Path("clinicdesk/app/queries/auditoria_accesos_queries.py"),
    Path("clinicdesk/app/queries/telemetria_eventos_queries.py"),
}

TABLAS_SENSIBLES = ("auditoria_accesos", "telemetria_eventos")
PATRON_SELECT_TABLA = re.compile(
    r"select\s+.+?\s+from\s+(auditoria_accesos|telemetria_eventos)\b",
    flags=re.IGNORECASE | re.DOTALL,
)


def test_no_hay_selects_fuera_de_queries_oficiales_para_tablas_sensibles() -> None:
    offenders: list[str] = []
    for ruta in sorted(BASE_APP.rglob("*.py")):
        contenido = ruta.read_text(encoding="utf-8")
        if not any(tabla in contenido for tabla in TABLAS_SENSIBLES):
            continue
        if not PATRON_SELECT_TABLA.search(contenido):
            continue
        if ruta in RUTAS_SELECT_PERMITIDAS:
            continue
        offenders.append(str(ruta))

    assert not offenders, (
        "Se detectaron lecturas SQL de auditoría/telemetría fuera de queries oficiales:\n"
        + "\n".join(offenders)
    )


def test_query_auditoria_aplica_saneo_de_campos_sensibles_en_lectura() -> None:
    ruta = Path("clinicdesk/app/queries/auditoria_accesos_queries.py")
    contenido = ruta.read_text(encoding="utf-8")

    assert 'sanear_valor_pii(row["usuario"], clave="usuario")' in contenido
    assert 'sanear_valor_pii(row["entidad_id"], clave="entidad_id")' in contenido


def test_query_telemetria_no_expone_columnas_sensibles_en_resumen() -> None:
    ruta = Path("clinicdesk/app/queries/telemetria_eventos_queries.py")
    contenido = ruta.read_text(encoding="utf-8").lower()
    select_telemetria = PATRON_SELECT_TABLA.search(contenido)

    assert select_telemetria is not None
    sentencia = select_telemetria.group(0)
    for columna_sensible in ("usuario", "contexto", "entidad_id", "payload", "detalle", "extra"):
        assert columna_sensible not in sentencia

