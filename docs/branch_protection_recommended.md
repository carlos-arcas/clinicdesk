# Branch protections recomendadas (main/master)

## Propósito

Esta guía evita tres riesgos frecuentes en repositorios colaborativos:

- merges a `main`/`master` sin pasar checks de calidad,
- regresiones por cambios no validados en CI,
- PRs aprobados sin revisión efectiva o con conversaciones abiertas.

La meta es que cada merge a ramas críticas conserve trazabilidad, revisión mínima y señal de calidad consistente.

## Configuración recomendada en GitHub

En GitHub, abrir **Settings → Branches → Branch protection rules → Add rule** y crear reglas para:

- `main`
- `master` (si existe en el repositorio)

Activar estas opciones en cada regla:

1. **Require a pull request before merging**
2. **Require approvals**: recomendado **1 aprobación**
3. **Dismiss stale approvals when new commits are pushed**
4. **Require conversation resolution before merging**
5. **Require status checks to pass before merging**
6. **Require branches to be up to date before merging** (recomendado)

Opcionales recomendados según política del equipo:

- **Require linear history**
- **Require signed commits** (solo si el equipo usa firma de commits)
- **Do not allow force pushes**
- **Do not allow deletions**

## Checks bloqueantes que sí deben ser required

El workflow de referencia es:

- `.github/workflows/quality_gate.yml` (**Quality Gate**)

En la sección de status checks required, configurar **solo**:

- `core (py3.11)`
- `core (py3.12)`

No marcar como required estos checks:

- `ui_smoke (non-blocking)`
- `uiqt (non-blocking)`
- `sandbox_gate (no-blocking)`

Motivo: estos jobs están definidos como informativos/no bloqueantes (`continue-on-error` o equivalente). Si se configuran como required, pueden bloquear merges por condiciones no críticas.

## Nota operativa: cuando “desaparecen” checks en un PR

Si un PR no muestra checks esperados, normalmente se debe a:

- commits con tokens como `[skip ci]` o `[ci skip]`,
- rama desactualizada que no contiene la versión actual del workflow.

Remedios recomendados:

1. Hacer `push` de un nuevo commit sin tokens de skip.
2. Ejecutar **Update branch** en el PR para re-sincronizar con la rama base.

## Política de merge recomendada

- **Squash merge** para PRs pequeños: deja historial compacto por feature/fix.
- **Rebase merge** si el equipo prioriza historial lineal y commits atómicos.
- **Auto-merge** opcional: útil para fusionar automáticamente cuando los checks required y revisiones ya están en verde.

