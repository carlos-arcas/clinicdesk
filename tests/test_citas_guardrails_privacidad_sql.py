from __future__ import annotations

from pathlib import Path

from clinicdesk.app.application.services.citas_privacidad_presentacion import FormateadorPrivacidadCitas
from clinicdesk.app.queries.citas_queries import CitaRow, CitasQueries


class _I18nFake:
    def t(self, key: str) -> str:
        catalogo = {
            "citas.riesgo.tooltip": "Riesgo de ausencia: {nivel}",
            "citas.tooltip.notas.sin": "Notas: sin contenido sensible",
            "citas.tooltip.notas.con": "Notas: contenido sensible oculto ({total} caracteres)",
        }
        return catalogo[key]


def test_no_sql_directo_en_ui_citas() -> None:
    rutas = Path("clinicdesk/app/pages/citas").rglob("*.py")
    patrones = (".execute(", "SELECT ")

    offenders: list[str] = []
    for ruta in rutas:
        contenido = ruta.read_text(encoding="utf-8")
        if any(patron in contenido for patron in patrones):
            offenders.append(ruta.as_posix())

    assert offenders == []


def test_tooltip_cita_no_expone_notas_completas() -> None:
    cita = CitaRow(
        id=9,
        inicio="2026-01-10 09:00:00",
        fin="2026-01-10 09:20:00",
        paciente_id=1,
        paciente_nombre="Paciente Ejemplo",
        medico_id=2,
        medico_nombre="Medico Ejemplo",
        sala_id=3,
        sala_nombre="Sala A",
        estado="PROGRAMADA",
        motivo="control privado",
        notas_len=78,
    )
    tooltip = FormateadorPrivacidadCitas().construir_tooltip_calendario(cita, _I18nFake(), "Medio")

    assert "control privado" not in tooltip
    assert "Notas: contenido sensible oculto (78 caracteres)" in tooltip


def test_query_listado_tiene_placeholders_y_sin_interpolacion() -> None:
    sql = CitasQueries._sql_listado()

    assert sql.count("?") >= 8
    assert "{" not in sql
    assert "}" not in sql
    assert "f\"" not in sql
