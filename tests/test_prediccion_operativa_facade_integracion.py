from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from clinicdesk.app.domain.citas import Cita
from clinicdesk.app.domain.enums import EstadoCita, TipoCita

pytestmark = [pytest.mark.integration]


def _seed_historial_y_agenda(container, seed_data: dict[str, int]) -> int:
    ahora = datetime.now().replace(second=0, microsecond=0)
    for indice in range(55):
        inicio = ahora - timedelta(days=30 - (indice % 10), hours=indice % 3)
        cita_id = container.citas_repo.create(
            Cita(
                paciente_id=seed_data["paciente_activo_id"],
                medico_id=seed_data["medico_activo_id"],
                sala_id=seed_data["sala_activa_id"],
                inicio=inicio,
                fin=inicio + timedelta(minutes=30),
                estado=EstadoCita.REALIZADA,
                motivo=f"Dataset operativo {indice}",
                tipo_cita=TipoCita.PRIMERA,
            )
        )
        container.connection.execute(
            """
            UPDATE citas
            SET check_in_at = ?,
                llamado_a_consulta_at = ?,
                consulta_inicio_at = ?,
                consulta_fin_at = ?
            WHERE id = ?
            """,
            (
                (inicio - timedelta(minutes=9)).strftime("%Y-%m-%d %H:%M:%S"),
                (inicio - timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S"),
                (inicio + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S"),
                (inicio + timedelta(minutes=24 + (indice % 4))).strftime("%Y-%m-%d %H:%M:%S"),
                cita_id,
            ),
        )
    futura = ahora + timedelta(days=2)
    futura_id = container.citas_repo.create(
        Cita(
            paciente_id=seed_data["paciente_activo_id"],
            medico_id=seed_data["medico_activo_id"],
            sala_id=seed_data["sala_activa_id"],
            inicio=futura,
            fin=futura + timedelta(minutes=20),
            estado=EstadoCita.PROGRAMADA,
            motivo="Agenda futura",
            tipo_cita=TipoCita.PRIMERA,
        )
    )
    container.connection.commit()
    return futura_id


def test_facade_prediccion_operativa_cubre_pipeline_minimo(container, seed_data) -> None:
    cita_futura_id = _seed_historial_y_agenda(container, seed_data)
    facade = container.prediccion_operativa_facade

    comprobacion = facade.comprobar_duracion_uc.ejecutar()
    entrenamiento = facade.entrenar_duracion_uc.ejecutar()
    predicciones = facade.previsualizar_duracion_uc.ejecutar(7)
    salud = facade.obtener_salud_duracion()
    explicacion = facade.obtener_explicacion_duracion(cita_futura_id, predicciones[cita_futura_id].nivel)

    assert comprobacion.apto_para_entrenar is True
    assert entrenamiento.ejemplos_usados >= 50
    assert cita_futura_id in predicciones
    assert predicciones[cita_futura_id].nivel in {"BAJO", "MEDIO", "ALTO"}
    assert salud.estado in {"VERDE", "AMARILLO"}
    assert explicacion.motivos_i18n_keys
    assert explicacion.acciones_i18n_keys
    assert explicacion.necesita_entrenar is False
