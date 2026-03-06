from __future__ import annotations

import json
from pathlib import Path


ESTADOS_PERMITIDOS = {
    "Verificada",
    "Parcial",
    "No verificada",
    "No implementada",
}


def test_checklist_funcional_tiene_estructura_minima_valida() -> None:
    ruta = Path("docs/features.json")
    assert ruta.exists(), "Debe existir docs/features.json como fuente estructurada del checklist funcional"

    data = json.loads(ruta.read_text(encoding="utf-8"))

    funciones = data.get("funciones")
    assert isinstance(funciones, list), "El checklist debe incluir una lista en `funciones`"
    assert funciones, "La lista `funciones` no puede estar vacía"

    ids = set()
    for indice, funcion in enumerate(funciones, start=1):
        assert isinstance(funcion, dict), f"funciones[{indice}] debe ser un objeto"

        for campo in ("id", "nombre", "descripcion", "prioridad", "estado_global", "desglose", "evidencias", "observaciones"):
            assert campo in funcion, f"funciones[{indice}] debe incluir el campo `{campo}`"

        function_id = funcion["id"]
        assert isinstance(function_id, str) and function_id.strip(), f"funciones[{indice}].id debe ser string no vacío"
        assert function_id not in ids, f"ID duplicado detectado: {function_id}"
        ids.add(function_id)

        assert funcion["estado_global"] in ESTADOS_PERMITIDOS, (
            f"funciones[{indice}].estado_global debe pertenecer a {sorted(ESTADOS_PERMITIDOS)}"
        )

        desglose = funcion["desglose"]
        assert isinstance(desglose, dict), f"funciones[{indice}].desglose debe ser objeto"
        for dimension in ("logica", "ui", "validaciones_seguridad", "e2e"):
            assert dimension in desglose, f"funciones[{indice}].desglose debe incluir `{dimension}`"
            assert desglose[dimension] in ESTADOS_PERMITIDOS, (
                f"funciones[{indice}].desglose.{dimension} debe pertenecer a {sorted(ESTADOS_PERMITIDOS)}"
            )

        evidencias = funcion["evidencias"]
        assert isinstance(evidencias, list) and evidencias, f"funciones[{indice}].evidencias debe ser lista no vacía"
        assert all(isinstance(item, str) and item.strip() for item in evidencias), (
            f"funciones[{indice}].evidencias debe contener strings no vacíos"
        )

    ruta_critica = data.get("ruta_critica_principal")
    assert isinstance(ruta_critica, list), "Debe existir `ruta_critica_principal` como lista"
    assert ruta_critica, "`ruta_critica_principal` no puede estar vacía"
    assert all(isinstance(item, str) for item in ruta_critica), "`ruta_critica_principal` debe contener IDs en texto"

    ids_invalidos = [item for item in ruta_critica if item not in ids]
    assert not ids_invalidos, f"La ruta crítica contiene IDs inexistentes: {ids_invalidos}"
