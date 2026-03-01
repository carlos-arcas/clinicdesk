# Historial de recetas: resumen de esquema real

## Tablas y relaciones detectadas

- `recetas` (principal): `id`, `paciente_id`, `medico_id`, `fecha`, `estado`, `observaciones`, `activo`.
- `receta_lineas` (detalle): `id`, `receta_id`, `medicamento_id`, `dosis`, `cantidad`, `pendiente`, `estado`, `duracion_dias`, `instrucciones`, `activo`.
- `medicamentos` (catálogo): `id`, `nombre_compuesto`, `nombre_comercial`, `activo`.
- `dispensaciones` (auditoría vinculada): `id`, `receta_id`, `receta_linea_id` (opcional), `medicamento_id`, `personal_id`, `fecha_hora`, `cantidad`, `activo`.

Relaciones clave:

- `recetas.paciente_id -> pacientes.id`.
- `recetas.medico_id -> medicos.id`.
- `receta_lineas.receta_id -> recetas.id`.
- `receta_lineas.medicamento_id -> medicamentos.id`.
- `dispensaciones.receta_id -> recetas.id`.
- `dispensaciones.receta_linea_id -> receta_lineas.id`.

## Consulta del historial en UI

Para el historial de paciente se usa **1 consulta SQL** (`LEFT JOIN`) que devuelve filas flat:

- columnas `receta_*`;
- columnas `linea_*`;
- nombre del medicamento unido desde `medicamentos`.

Con ese resultado, aplicación agrupa en memoria:

- lista de recetas ordenadas por fecha DESC;
- diccionario de líneas por `receta_id`.

## Derivación de “medicaciones activas”

Se deriva de forma conservadora usando campos existentes:

- estado de receta (`recetas.estado`),
- estado de línea (`receta_lineas.estado`),
- presencia de líneas activas no anuladas/finalizadas.

No existe fecha de fin explícita por línea en el esquema actual; por ello se representa `Fin` con duración (`duracion_dias`) o `—` cuando no aplica.
