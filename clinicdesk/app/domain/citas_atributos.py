from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AtributoCita:
    clave: str
    etiqueta: str


ATRIBUTOS_CITA: tuple[AtributoCita, ...] = (
    AtributoCita(clave="fecha", etiqueta="Fecha"),
    AtributoCita(clave="hora_inicio", etiqueta="Hora inicio"),
    AtributoCita(clave="hora_fin", etiqueta="Hora fin"),
    AtributoCita(clave="paciente", etiqueta="Paciente"),
    AtributoCita(clave="medico", etiqueta="Médico"),
    AtributoCita(clave="sala", etiqueta="Sala"),
    AtributoCita(clave="estado", etiqueta="Estado"),
    AtributoCita(clave="notas_len", etiqueta="Notas len"),
    AtributoCita(clave="incidencias", etiqueta="Incidencias"),
)


def claves_atributos_cita() -> tuple[str, ...]:
    return tuple(atributo.clave for atributo in ATRIBUTOS_CITA)
