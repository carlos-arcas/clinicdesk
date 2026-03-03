from __future__ import annotations

from clinicdesk.app.application.ports.recordatorios_citas_port import (
    DatosRecordatorioCitaDTO,
    EstadoRecordatorioDTO,
)
from clinicdesk.app.application.usecases.recordatorios_citas import (
    MarcarRecordatoriosEnviadosEnLote,
    PrepararRecordatorioCita,
    PrepararRecordatoriosEnLote,
)


class _FakePort:
    def __init__(
        self,
        dto: DatosRecordatorioCitaDTO | None,
        contactos: dict[int, tuple[str | None, str | None]] | None = None,
        estados_lote: dict[tuple[int, str], str] | None = None,
    ) -> None:
        self._dto = dto
        self._contactos = contactos or {}
        self._estados_lote = estados_lote or {}
        self.upsert_lote_calls: list[list[tuple[int, str, str, str]]] = []

    def obtener_datos_recordatorio_cita(self, cita_id: int) -> DatosRecordatorioCitaDTO | None:
        return self._dto

    def upsert_recordatorio_cita(self, cita_id: int, canal: str, estado: str, now_utc: str) -> None:
        return None

    def obtener_estado_recordatorio(self, cita_id: int) -> tuple[EstadoRecordatorioDTO, ...]:
        return tuple()

    def obtener_contacto_citas(self, cita_ids: tuple[int, ...]) -> dict[int, tuple[str | None, str | None]]:
        return {cita_id: self._contactos.get(cita_id, (None, None)) for cita_id in cita_ids}

    def obtener_estado_recordatorio_lote(self, cita_ids: tuple[int, ...]) -> dict[tuple[int, str], str]:
        return {k: v for k, v in self._estados_lote.items() if k[0] in cita_ids}

    def upsert_recordatorios_lote(self, items: list[tuple[int, str, str, str]]) -> int:
        self.upsert_lote_calls.append(items)
        for cita_id, canal, estado, _ in items:
            self._estados_lote[(cita_id, canal)] = estado
        return len(items)


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


def test_preparar_recordatorios_en_lote_omite_sin_contacto_y_ya_enviado() -> None:
    fake = _FakePort(
        None,
        contactos={1: ("600", "a@x.com"), 2: (None, "b@x.com"), 3: ("700", "c@x.com")},
        estados_lote={(3, "WHATSAPP"): "ENVIADO"},
    )
    uc = PrepararRecordatoriosEnLote(fake)

    resultado = uc.ejecutar((1, 2, 3), "WHATSAPP")

    assert resultado.preparadas == 1
    assert resultado.omitidas_sin_contacto == 1
    assert resultado.omitidas_ya_enviado == 1


def test_marcar_enviados_en_lote_es_idempotente() -> None:
    fake = _FakePort(None)
    uc = MarcarRecordatoriosEnviadosEnLote(fake)

    primero = uc.ejecutar((10, 11), "EMAIL")
    segundo = uc.ejecutar((10, 11), "EMAIL")

    assert primero.enviadas == 2
    assert segundo.enviadas == 2
    assert fake._estados_lote[(10, "EMAIL")] == "ENVIADO"
    assert fake._estados_lote[(11, "EMAIL")] == "ENVIADO"


def test_preparar_recordatorios_en_lote_preparado_es_idempotente() -> None:
    fake = _FakePort(
        None,
        contactos={1: ("600", "a@x.com")},
        estados_lote={(1, "WHATSAPP"): "PREPARADO"},
    )
    uc = PrepararRecordatoriosEnLote(fake)

    resultado = uc.ejecutar((1,), "WHATSAPP")

    assert resultado.preparadas == 1
    assert resultado.omitidas_sin_contacto == 0
    assert resultado.omitidas_ya_enviado == 0

