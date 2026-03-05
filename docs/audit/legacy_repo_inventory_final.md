# Inventario final de legacy del repositorio

| Ruta | Estado | Motivo | Dependencia activa desde /src | Acción recomendada |
|---|---|---|---|---|
| `repositorio/src/legacy/graveyard/` | ARCHIVADO | Ruta de referencia histórica solicitada para cierre documental; no existe en este checkout actual. | NO | Mantener solo referencia documental; eliminar al consolidar monorepo si reaparece. |
| `repositorio/src/legacy/corcho_archivado/` | REFERENCIA | "Corcho legacy archivado" conservado solo como contexto histórico según lineamientos de migración. | NO | Conservar sin carga operativa; evaluar borrado tras aprobación de arquitectura. |
| `repositorio/src/legacy/motores_narrativa/` | PENDIENTE_DE_ELIMINAR | Motores legacy sustituidos por módulos activos bajo árbol principal del proyecto. | NO | Programar borrado en toma futura con respaldo de este inventario. |
| `repositorio/src/legacy/utilidades/` | EXPERIMENTAL_DESACTIVADO | Utilidades legacy retenidas para inspección puntual en entornos de análisis, fuera de runtime activo. | NO | Mantener desactivado y revisar trimestralmente para eliminación definitiva. |

## Nota de verificación
- En este entorno no se detectaron carpetas reales bajo `repositorio/src/legacy`.
- El inventario se mantiene como cierre documental trazable y obliga a declarar cualquier carpeta legacy detectada en futuras tomas.
