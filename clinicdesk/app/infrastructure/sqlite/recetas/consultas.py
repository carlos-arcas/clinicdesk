from __future__ import annotations

from clinicdesk.app.domain.exceptions import ValidationError


def construir_consulta_por_actor(
    *,
    campo_actor: str,
    actor_id: int,
    desde: str | None,
    hasta: str | None,
) -> tuple[str, list[object]]:
    if actor_id <= 0:
        raise ValidationError(f"{campo_actor}_id inválido.")

    clauses = [f"{campo_actor}_id = ?", "activo = 1"]
    params: list[object] = [actor_id]

    if desde:
        clauses.append("fecha >= ?")
        params.append(desde)
    if hasta:
        clauses.append("fecha <= ?")
        params.append(hasta)

    sql = "SELECT * FROM recetas WHERE " + " AND ".join(clauses) + " ORDER BY fecha DESC"
    return sql, params
