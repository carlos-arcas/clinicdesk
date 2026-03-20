from __future__ import annotations

from datetime import datetime, timedelta

from clinicdesk.app.domain.citas import Cita
from clinicdesk.app.domain.enums import EstadoCita, TipoCita

FECHA_BASE_CITAS = datetime(2024, 5, 20, 9, 0, 0)
FECHA_BASE_PREDICCION = datetime(2026, 4, 15, 9, 0, 0)


def obtener_fecha_base_prediccion() -> datetime:
    return FECHA_BASE_PREDICCION


def crear_cita_programada(
    container, seed_data: dict[str, int], inicio: datetime, *, motivo: str = "Seguimiento"
) -> int:
    fin = inicio + timedelta(minutes=30)
    return container.citas_repo.create(
        Cita(
            paciente_id=seed_data["paciente_activo_id"],
            medico_id=seed_data["medico_activo_id"],
            sala_id=seed_data["sala_activa_id"],
            inicio=inicio,
            fin=fin,
            estado=EstadoCita.PROGRAMADA,
            motivo=motivo,
            tipo_cita=TipoCita.PRIMERA,
        )
    )


def seed_historial_y_agenda_prediccion(
    container,
    seed_data: dict[str, int],
    *,
    ahora: datetime | None = None,
    total_historicas: int = 60,
) -> int:
    base = (ahora or obtener_fecha_base_prediccion()).replace(second=0, microsecond=0)
    for indice in range(total_historicas):
        inicio = base - timedelta(days=45 - (indice % 15), hours=indice % 4, minutes=(indice % 3) * 10)
        cita_id = container.citas_repo.create(
            Cita(
                paciente_id=seed_data["paciente_activo_id"],
                medico_id=seed_data["medico_activo_id"],
                sala_id=seed_data["sala_activa_id"],
                inicio=inicio,
                fin=inicio + timedelta(minutes=30),
                estado=EstadoCita.REALIZADA,
                motivo=f"Histórica {indice}",
                tipo_cita=TipoCita.PRIMERA,
            )
        )
        check_in = inicio - timedelta(minutes=12)
        llamado = inicio - timedelta(minutes=4)
        consulta_inicio = inicio + timedelta(minutes=2)
        consulta_fin = consulta_inicio + timedelta(minutes=18 + (indice % 5))
        container.connection.execute(
            """
            UPDATE citas
            SET check_in_at = ?,
                llamado_a_consulta_at = ?,
                consulta_inicio_at = ?,
                consulta_fin_at = ?,
                check_out_at = ?
            WHERE id = ?
            """,
            (
                check_in.strftime("%Y-%m-%d %H:%M:%S"),
                llamado.strftime("%Y-%m-%d %H:%M:%S"),
                consulta_inicio.strftime("%Y-%m-%d %H:%M:%S"),
                consulta_fin.strftime("%Y-%m-%d %H:%M:%S"),
                (consulta_fin + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                cita_id,
            ),
        )
    futura_id = crear_cita_programada(container, seed_data, base + timedelta(days=1, hours=2), motivo="Agenda futura")
    container.connection.commit()
    return futura_id
