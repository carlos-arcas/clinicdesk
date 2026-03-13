from __future__ import annotations

INSERT_RECETA = """
INSERT INTO recetas (
    paciente_id, medico_id, fecha, observaciones
)
VALUES (?, ?, ?, ?)
"""

UPDATE_RECETA = """
UPDATE recetas SET
    paciente_id = ?,
    medico_id = ?,
    fecha = ?,
    observaciones = ?
WHERE id = ?
"""

INSERT_LINEA = """
INSERT INTO receta_lineas (
    receta_id, medicamento_id, dosis, duracion_dias, instrucciones
)
VALUES (?, ?, ?, ?, ?)
"""

UPDATE_LINEA = """
UPDATE receta_lineas SET
    receta_id = ?,
    medicamento_id = ?,
    dosis = ?,
    duracion_dias = ?,
    instrucciones = ?
WHERE id = ?
"""

SELECT_LINEAS_ACTIVAS = """
SELECT * FROM receta_lineas
WHERE receta_id = ? AND activo = 1
ORDER BY id
"""
