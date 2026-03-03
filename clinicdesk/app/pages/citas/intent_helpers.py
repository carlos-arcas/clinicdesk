from __future__ import annotations


def buscar_indice_por_cita_id(citas_ids: list[int], cita_id: int) -> int | None:
    for indice, actual in enumerate(citas_ids):
        if actual == cita_id:
            return indice
    return None
