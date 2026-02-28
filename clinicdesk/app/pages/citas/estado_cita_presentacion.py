from __future__ import annotations

from clinicdesk.app.domain.enums import EstadoCita


ESTADOS_FILTRO_CITAS: list[tuple[str, str]] = [
    ("Programada", EstadoCita.PROGRAMADA.value),
    ("Cancelada", EstadoCita.CANCELADA.value),
    ("Realizada", EstadoCita.REALIZADA.value),
    ("No asistió", EstadoCita.NO_PRESENTADO.value),
    ("Todos", "TODOS"),
]


def etiqueta_estado_cita(estado: str) -> str:
    mapa = {
        EstadoCita.PROGRAMADA.value: "Programada",
        EstadoCita.CANCELADA.value: "Cancelada",
        EstadoCita.REALIZADA.value: "Realizada",
        EstadoCita.NO_PRESENTADO.value: "No asistió",
    }
    return mapa.get(estado, estado.replace("_", " ").title())
