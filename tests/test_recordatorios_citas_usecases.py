from __future__ import annotations

from clinicdesk.app.application.ports.recordatorios_citas_port import (
    DatosRecordatorioCitaDTO,
    EstadoRecordatorioDTO,
)
from clinicdesk.app.application.usecases.recordatorios_citas import PrepararRecordatorioCita


class _FakePort:
    def __init__(self, dto: DatosRecordatorioCitaDTO | None) -> None:
        self._dto = dto

    def obtener_datos_recordatorio_cita(self, cita_id: int) -> DatosRecordatorioCitaDTO | None:
        return self._dto

    def upsert_recordatorio_cita(self, cita_id: int, canal: str, estado: str, now_utc: str) -> None:
        return None

    def obtener_estado_recordatorio(self, cita_id: int) -> tuple[EstadoRecordatorioDTO, ...]:
        return tuple()


def _t(key: str) -> str:
    textos = {
        "recordatorio.advertencia.falta_telefono": "Falta teléfono en la ficha del paciente.",
        "recordatorio.advertencia.falta_email": "Falta correo en la ficha del paciente.",
        "recordatorio.error.no_encontrada": "No existe",
        "recordatorio.plantilla.whatsapp": "Hola {paciente}, {fecha} {hora} {clinica} {medico}",
        "recordatorio.plantilla.email": "Hola {paciente}, {fecha} {hora} {clinica} {medico}",
        "recordatorio.plantilla.llamada": "Hola {paciente}, {fecha} {hora} {clinica} {medico}",
        "recordatorio.clinica.por_defecto": "la clínica",
        "recordatorio.medico.no_disponible": "equipo médico",
    }
    return textos[key]


def test_preparar_recordatorio_con_contacto_puede_copiar() -> None:
    uc = PrepararRecordatorioCita(
        _FakePort(
            DatosRecordatorioCitaDTO(
                cita_id=1,
                inicio="2026-01-02T10:30:00",
                paciente_nombre="Ana Pérez",
                telefono="600000000",
                email="ana@test.com",
                medico_nombre="Dr. López",
            )
        )
    )

    preview = uc.ejecutar(1, "WHATSAPP", _t)

    assert preview.puede_copiar is True
    assert preview.advertencias == tuple()
    assert "Ana Pérez" in preview.mensaje


def test_preparar_recordatorio_whatsapp_sin_telefono_bloquea_copia() -> None:
    uc = PrepararRecordatorioCita(
        _FakePort(
            DatosRecordatorioCitaDTO(
                cita_id=1,
                inicio="2026-01-02T10:30:00",
                paciente_nombre="Ana Pérez",
                telefono=None,
                email="ana@test.com",
                medico_nombre="Dr. López",
            )
        )
    )

    preview = uc.ejecutar(1, "LLAMADA", _t)

    assert preview.puede_copiar is False
    assert preview.advertencias == ("Falta teléfono en la ficha del paciente.",)


def test_preparar_recordatorio_email_sin_correo_bloquea_copia() -> None:
    uc = PrepararRecordatorioCita(
        _FakePort(
            DatosRecordatorioCitaDTO(
                cita_id=1,
                inicio="2026-01-02T10:30:00",
                paciente_nombre="Ana Pérez",
                telefono="600000000",
                email=None,
                medico_nombre="Dr. López",
            )
        )
    )

    preview = uc.ejecutar(1, "EMAIL", _t)

    assert preview.puede_copiar is False
    assert preview.advertencias == ("Falta correo en la ficha del paciente.",)
