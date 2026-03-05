# Cierre real de storage legacy por proyecto (modo operador)

## Precondiciones
- Ejecutar desde la raíz del repositorio.
- Tener Python 3.11+ disponible.
- Confirmar que los proyectos locales estén bajo `data/proyectos/<id_proyecto>/`.
- Verificar permisos de escritura en `data/backups/storage_legacy_quarantine/`.

## Comandos operativos (orden obligatorio)
1. Auditoría inicial:
   ```bash
   python scripts/auditar_storage_legacy_por_proyecto.py
   ```
2. Simulación segura de limpieza:
   ```bash
   python scripts/limpiar_storage_legacy_por_proyecto.py --dry-run
   ```
3. Ejecución real (solo cuando corresponda):
   ```bash
   python scripts/limpiar_storage_legacy_por_proyecto.py --apply
   ```
4. Verificación de cierre:
   ```bash
   python scripts/verificar_cierre_storage_legacy.py
   ```

## Interpretación de estados
- `SOLO_LEGACY`: solo existe `storage_legacy`.
- `SOLO_NUEVO`: solo existe `storage`.
- `AMBOS`: existen `storage_legacy` y `storage`.
- `NINGUNO`: no existe ninguno de los dos directorios.

## Regla operativa
- **Solo limpiar proyectos en estado `AMBOS`.**
- No ejecutar `--apply` sobre `SOLO_LEGACY`, `SOLO_NUEVO` o `NINGUNO`.

## Backup / quarantine
- Ubicación: `data/backups/storage_legacy_quarantine/<timestamp_utc>/<proyecto>/storage_legacy/`.
- El movimiento a quarantine ocurre únicamente con `--apply`.

## Reversión manual desde backup
1. Identificar el último timestamp de backup para el proyecto afectado.
2. Copiar de vuelta la carpeta `storage_legacy` al proyecto:
   ```bash
   cp -R data/backups/storage_legacy_quarantine/<timestamp>/<proyecto>/storage_legacy \
     data/proyectos/<proyecto>/storage_legacy
   ```
3. Re-ejecutar auditoría para confirmar estado esperado:
   ```bash
   python scripts/auditar_storage_legacy_por_proyecto.py
   ```

## Resultado esperado por operación
- Sin datos locales en `data/proyectos`, la operación queda como **tooling listo**.
- Con datos locales y casos `AMBOS`, el cierre real debe eliminar `AMBOS` tras `--apply` y verificación final.
