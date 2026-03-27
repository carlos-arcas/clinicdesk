# Roadmap operativo Codex (fuente de verdad)

> Documento operativo y atómico para ejecuciones autónomas.
> Regla de selección: tomar siempre la primera tarea `TODO` no bloqueada.
> Histórico narrativo complementario: `docs/roadmap_codex_automation.md`.

## Relación con el histórico narrativo

- `docs/roadmap_codex.md` define el backlog seleccionable y el estado vigente de cada tarea.
- `docs/roadmap_codex_automation.md` conserva contexto narrativo de ciclos previos, pero no reordena ni sustituye este roadmap.
- Si un “Siguiente paso recomendado” del histórico sigue vigente, primero debe materializarse aquí como tarea `TODO` antes de poder ejecutarse.
- Si ambos documentos divergen, prevalece este roadmap operativo.

## Estado seleccionable actual

- 2026-03-27 20:33:36Z: `RCDX-005 - Registrar backlog sin tarea seleccionable` sigue en `BLOCKED`. La revalidacion confirma que el roadmap operativo sigue sin ninguna tarea `TODO` ni `WIP` elegible y no aparece evidencia nueva de bug critico, test roto o error de ejecucion que justifique abrir prioridad fuera de backlog: `python -m scripts.gate_rapido` vuelve a pasar (`rc=0`) y el unico bloqueo vigente es `python -m scripts.gate_pr`, que aborta en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`. `git ls-files data` y `git status --short data` siguen vacios, `git check-ignore -v` confirma que ambas SQLite estan ignoradas por `.gitignore:8 (data/)` y `Get-ChildItem data` las identifica como artefactos locales del worktree. Por prohibicion contractual de tocar binarios locales en esta ejecucion, no se materializa tarea nueva ni se altera codigo de producto. El siguiente paso exacto es cerrar cualquier proceso que regenere esas SQLite y ejecutar `python -m scripts.gate_pr` en un workspace limpio equivalente sin `data\clinicdesk.db` ni `data\clinicdesk.sqlite`; solo entonces corresponde rematerializar la primera `TODO` real del roadmap.

- 2026-03-27 20:14:14Z: `RCDX-005 - Registrar backlog sin tarea seleccionable` sigue en `BLOCKED`. La revalidacion confirma que el roadmap operativo ya no tiene ninguna tarea `TODO` ni `WIP` elegible: todas las entradas seleccionables estan en `BLOCKED`, `python -m scripts.gate_rapido` vuelve a pasar (`rc=0`) y no aparece evidencia nueva de bug critico ni de tests rotos que justifique abrir trabajo funcional fuera de backlog. `python -m scripts.gate_pr` sigue abortando en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`; `git ls-files data` y `git status --short data` no listan esos SQLite, por lo que el bloqueo viene de artefactos locales ignorados del worktree. Por prohibicion contractual de tocar binarios locales en esta ejecucion, no se materializa tarea nueva ni se altera codigo de producto. El siguiente paso exacto es cerrar cualquier proceso que regenere esas SQLite, ejecutar `python -m scripts.gate_pr` en un workspace limpio equivalente sin `data\clinicdesk.db` y `data\clinicdesk.sqlite`, y solo entonces rematerializar la primera `TODO` real del roadmap.

- 2026-03-27 20:58:07Z: `RCDX-041 - Aterrizar una implementacion usable y honesta de Seguro clínica` queda en `BLOCKED`. La ejecucion confirma que el workspace ya no se presenta como pantalla vacia: `clinicdesk/app/pages/seguros/workspace_navegacion.py` abre por defecto en `cartera`, `clinicdesk/app/pages/seguros/page.py` hidrata el workspace durante `_retranslate()` y `clinicdesk/app/pages/seguros/page_actions_comercial.py` rellena `estado_comercial` y `renovaciones` con mensajes honestos incluso cuando no hay oportunidad activa. La regresion nueva en `tests/test_bootstrap_ui_resiliencia.py` valida con SQLite temporal que `PageSeguros` arranca en `cartera` y deja los labels clave con contenido i18n no placeholder, mientras `tests/application/seguros/test_workspace_navegacion.py` congela el nuevo default de navegacion. `.\.venv\Scripts\python.exe -m pytest -q tests/application/seguros` pasa (`55 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_bootstrap_ui_resiliencia.py` pasa (`7 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` vuelve a abortar en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`, artefactos binarios fuera de alcance en esta ejecucion. El siguiente paso exacto es retirar temporalmente esos SQLite del arbol del repo o ejecutar `python -m scripts.gate_pr` en un workspace limpio equivalente, reintentarlo sobre `RCDX-041` y, cuando quede libre el bloqueo operativo, continuar con la siguiente `TODO` real.

- 2026-03-27 20:54:43Z: `RCDX-041 - Aterrizar una implementacion usable y honesta de Seguro clínica` pasa a `WIP`. Sigue siendo la primera tarea `TODO` elegible real porque `.\.venv\Scripts\python.exe -m pytest -q tests/application/seguros` pasa (`54 passed`), no aparece evidencia nueva de bug critico ni de tests rotos fuera de `seguros`, y la auditoria de `clinicdesk/app/pages/seguros/page.py`, `clinicdesk/app/pages/seguros/workspace_navegacion.py` y `clinicdesk/app/pages/seguros/page_actions_comercial.py` confirma un defecto acotado de UX/wiring: el workspace abre en `preventa` y deja paneles clave en `"-"` porque no ejecuta `refrescar_cartera()` al construir la pantalla, por lo que se percibe como modulo no implementado aunque la capa de aplicacion ya sea operable.

- 2026-03-27 20:52:57Z: `RCDX-042 - Hacer verosimil el seed demo para poblar BBDD util en pantallas y ML` sigue en `BLOCKED`. La ejecucion final ya deja datos demo verosimiles de extremo a extremo: `clinicdesk/app/application/demo_data/catalogos.py` y `clinicdesk/app/application/demo_data/generator.py` sustituyen placeholders evidentes por catalogos y reglas deterministas mas naturales; `clinicdesk/app/infrastructure/sqlite/demo_seed/contexto_agenda_ml.py` y `clinicdesk/app/infrastructure/sqlite/demo_seed/operational_history.py` enriquecen las citas con `tipo_cita`, `canal_reserva`, `override_fecha_hora`, trazas de agenda y seguimiento ML persistido; `scripts/ml_cli.py` y `seed_demo_data.py` pasan a usar una ventana temporal alrededor de la fecha actual y el wrapper ya propaga `--confirm-reset`. `.\.venv\Scripts\python.exe -m pytest -q tests/test_demo_data_generator.py tests/test_demo_data_seeder_sqlite.py tests/test_seed_demo_empty_modules.py tests/test_ml_cli_smoke.py` pasa (`13 passed`), `python -m scripts.gate_rapido` devuelve `rc=0` y la resembra externa `.\.venv\Scripts\python.exe seed_demo_data.py --sqlite-path C:\Users\arcas\AppData\Local\ClinicDesk\clinicdesk_demo.sqlite --reset --confirm-reset RESET-DEMO` devuelve `rc=0`, dejando `25` medicos, `500` pacientes, `12` personas de staff, `5000` citas, `732` incidencias, `7711` recordatorios, `5000` predicciones y `2601` acciones ML con `5000` citas enriquecidas. El cierre contractual sigue bloqueado porque `python -m scripts.gate_pr` vuelve a abortar en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`; el siguiente paso exacto es retirar temporalmente esos SQLite del arbol del repo o ejecutar el gate completo en un workspace limpio equivalente, reintentarlo sobre `RCDX-042` y, cuando quede libre el bloqueo operativo, continuar con `RCDX-041`.

- 2026-03-27 20:42:53Z: `RCDX-042 - Hacer verosimil el seed demo para poblar BBDD util en pantallas y ML` queda en `BLOCKED`. La ejecucion deja congelado el contrato visible del generador con `tests/test_demo_data_generator.py` para evitar volver a dominios `*.demo`, direcciones de placeholder o notas repetitivas, y completa el seeder con `clinicdesk/app/infrastructure/sqlite/demo_seed/operational_history.py`, que ahora rellena `recordatorios_citas`, `predicciones_ausencias_log` y `ml_acciones_operativas` a partir de las citas persistidas sin salir de infraestructura. `.\.venv\Scripts\python.exe -m pytest -q tests/test_demo_data_generator.py tests/test_demo_data_seeder_sqlite.py tests/test_seed_demo_empty_modules.py` pasa (`7 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_ml_cli_smoke.py` pasa (`5 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` sigue abortando en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`, artefactos binarios fuera de alcance en esta ejecucion. El siguiente paso exacto es retirar temporalmente esos SQLite del arbol del repo o ejecutar `python -m scripts.gate_pr` en un workspace limpio equivalente, reintentarlo sobre `RCDX-042` y, cuando quede libre el bloqueo operativo, continuar con `RCDX-041`.

- 2026-03-27 19:26:01Z: `RCDX-042 - Hacer verosimil el seed demo para poblar BBDD util en pantallas y ML` pasa a `WIP`. La prioridad real cambia por peticion explicita de usuario final: la base actual necesita datos creibles para probar pantallas y ML, y la inspeccion de `clinicdesk/app/application/demo_data/generator.py` confirma que el seed vigente sigue generando patrones claramente artificiales (`Calle Salud {n}`, emails `@clinicdesk.demo`/`@paciente.demo`, motivos/notas ciclicos y una unica incidencia `CITA_FUERA_TURNO` con textos de demo), ademas de no poblar historicos persistidos como `predicciones_ausencias_log`, `recordatorios_citas` y `ml_acciones_operativas` que varias vistas consumen. Por contrato, se materializa una tarea atomica por delante de `RCDX-041` para ajustar el generador y el seeder a datos mas naturales y utiles antes de resembrar la BBDD local.

- 2026-03-27 20:14:48Z: `RCDX-038 - Alinear tests/test_prediccion_ausencias_page_entrenamiento_handlers.py con la inicializacion segura de PagePrediccionAusencias` queda en `BLOCKED`. `tests/test_prediccion_ausencias_page_entrenamiento_handlers.py` pasa tras sustituir `object.__new__(PagePrediccionAusencias)` por una construccion segura basada en `QApplication` minima y `PagePrediccionAusencias.__new__(PagePrediccionAusencias)`, y alinear `test_on_entrenar_ok_refresca_componentes_clave` con el contrato actual de `_on_entrenar_ok(...)`, que tambien refresca `_actualizar_resumen_modelo()`. `.\.venv\Scripts\python.exe -m pytest -q tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` sigue en verde (`3 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_prediccion_ausencias_coordinador_entrenamiento.py` sigue en verde (`4 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` vuelve a abortar en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`, artefactos binarios fuera de alcance en esta ejecucion. El siguiente paso exacto es retirar temporalmente esos SQLite del arbol del repo o ejecutar `python -m scripts.gate_pr` en un workspace limpio equivalente, reintentarlo sobre `RCDX-038` y, cuando quede libre el bloqueo operativo, continuar con `RCDX-041`.

- 2026-03-27 20:13:01Z: `RCDX-038 - Alinear tests/test_prediccion_ausencias_page_entrenamiento_handlers.py con la inicializacion segura de PagePrediccionAusencias` pasa a `WIP`. Sigue siendo la primera tarea `TODO` elegible real porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_entrenamiento_handlers.py` sigue reproduciendo tres fallos acotados al helper `_page_minima()` por `TypeError: object.__new__(PagePrediccionAusencias) is not safe, use PagePrediccionAusencias.__new__()`, mientras `tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` y `tests/ui/test_prediccion_ausencias_coordinador_entrenamiento.py` permanecen como cobertura especifica del area. El bloqueo operativo ya conocido de `python -m scripts.gate_pr` por `data\clinicdesk.db` y `data\clinicdesk.sqlite` sigue vigente, pero no introduce una prioridad funcional superior dentro del backlog ni invalida la correccion focal de la suite de handlers.

- 2026-03-27 17:43:41Z: `RCDX-040 - Corregir layout critico desktop y recuperar modulos operativos bloqueados` queda en `BLOCKED`. Se valida el recorte de producto comprometido: `MainWindow` envuelve el `stack` en un contenedor scrollable sin romper `window.stack.currentWidget()`, `EstadoPantallaWidget` deja el contenido anclado arriba, `Pacientes` reajusta columnas para evitar encabezados truncados, `Citas` sustituye las pestañas visibles por un layout vertical con calendario compacto arriba y lista abajo, y `Médicos`/`Personal` vuelven a cargar al eliminar el import incompatible de `QPointer`; además `clinicdesk/app/queries/citas_queries.py` se hace compatible con esquemas que aún no exponen `citas.riesgo_ausencia`, `AppContainer.close()` y `tests/conftest.py` cierran conexiones SQLite por hilo para evitar el bloqueo de teardown, y la ruta de humo de `Predicción operativa` se alinea con el toggle real `chk_mostrar_agenda`. La revalidacion focal `.\.venv\Scripts\python.exe -m pytest -q tests/test_bootstrap_ui_resiliencia.py tests/test_citas_listado_queries.py tests/test_estado_pantalla_widget.py tests/test_main_window_scroll_layout.py tests/ui/test_estado_pantalla_widget_qt.py tests/ui/test_citas_coordinadores.py tests/ui/test_citas_security_ui.py tests/ui/test_ruta_critica_desktop_smoke.py` pasa (`32 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` sigue abortando en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`, artefactos binarios fuera de alcance en esta ejecucion. El siguiente paso exacto es retirar temporalmente esos SQLite del arbol del repo o ejecutar `python -m scripts.gate_pr` en un workspace limpio equivalente y reintentarlo; `Seguro clínica` queda planificado como `RCDX-041`.

- 2026-03-27 17:15:39Z: `RCDX-040 - Corregir layout critico desktop y recuperar modulos operativos bloqueados` pasa a `WIP`. La prioridad real cambia por evidencia nueva de producto aportada por usuario final con capturas de la app desktop: faltan barras de desplazamiento vertical en pantallas largas y los controles inferiores colapsan fuera del viewport; la tabla de `Pacientes` aparece anclada demasiado abajo y con encabezados recortados; `Citas` debe pasar de dos pestañas a un layout con calendario compacto arriba y lista abajo; `Médicos` y `Personal` fallan al cargar; y `Seguro clínica` se reporta como no implementado de forma usable. La inspeccion de `clinicdesk/app/ui/main_window.py`, `clinicdesk/app/ui/widgets/estado_pantalla_widget.py`, `clinicdesk/app/pages/citas/page.py`, `clinicdesk/app/pages/medicos/dialogs/medico_form.py` y `clinicdesk/app/pages/personal/dialogs/personal_form.py` confirma un recorte atómico viable: el shell principal no envuelve el stack en ningun contenedor scrollable, `EstadoPantallaWidget` coloca el contenido despues de un `stretch` que lo empuja al fondo, `PageCitas` sigue acoplada a `QTabWidget`, y tanto `medico_form.py` como `personal_form.py` importan `QPointer` desde `PySide6.QtCore`, origen directo del `import_error` mostrado por los placeholders. Por contrato, se materializa una tarea de producto por delante de `RCDX-038`, dejando `Seguro clínica` para roadmap si no cabe en esta ronda.

- 2026-03-27 16:55:29Z: `RCDX-039 - Restablecer la apertura de MainWindow tras login valido` queda en `BLOCKED`. La correccion funcional queda validada porque una reproduccion controlada con `QT_QPA_PLATFORM=offscreen` y `.\.venv\Scripts\python.exe` ya construye `MainWindow` sin excepcion, `.\.venv\Scripts\python.exe -m pytest -q tests/test_producto_final_sin_demo.py tests/test_main_window_csv_refresh.py tests/test_main_post_login_window_open.py` pasa (`8 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` ahora falla en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por el artefacto local `data\clinicdesk.db`, que es ajeno al fix y no debe tocarse automaticamente en esta ejecucion. El siguiente paso exacto es retirar temporalmente ese SQLite del arbol del repo o ejecutar el gate completo en un workspace limpio equivalente, reintentar `python -m scripts.gate_pr` y, cuando quede libre el bloqueo operativo, retomar `RCDX-038` como siguiente `TODO` funcional.

- 2026-03-27 16:50:01Z: `RCDX-039 - Restablecer la apertura de MainWindow tras login valido` pasa a `WIP`. La prioridad real cambia por evidencia nueva de bug critico de producto: al reproducir el login con credenciales validas, `logs/app.log` confirma `auth_login_success`, `auth_login_accepted` y `main_window_create`, pero la transicion post-login termina en `post_login_transition_fail`; ademas, una reproduccion controlada con `.\.venv\Scripts\python.exe` confirma `AttributeError: 'MainWindow' object has no attribute '_on_csv_imported'` en `clinicdesk/app/ui/main_window.py:91`, por lo que antes de retomar `RCDX-038` hay que restaurar el callback CSV que hoy rompe la creacion de la ventana principal.

- 2026-03-27 16:34:47Z: `RCDX-037 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/toolchain.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`13 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py`. La prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_entrenamiento_handlers.py` falla en tres tests con `TypeError: object.__new__(PagePrediccionAusencias) is not safe, use PagePrediccionAusencias.__new__()`, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` pasa (`3 passed`) y `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_prediccion_ausencias_coordinador_entrenamiento.py` pasa (`4 passed`), por lo que se materializa `RCDX-038 - Alinear tests/test_prediccion_ausencias_page_entrenamiento_handlers.py con la inicializacion segura de PagePrediccionAusencias` como primera `TODO` no bloqueada y se deja la deuda de Ruff del guardrail para una ejecucion posterior.

- 2026-03-27 16:27:18Z: `RCDX-037 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/toolchain.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` mantiene una unica deuda de formato acotada a la comprension de `faltantes` dentro de `_leer_versiones_lock(...)`, `tests/test_toolchain_diagnostico.py`, `tests/test_entorno_python.py` y `tests/test_gate_pr.py` siguen identificados como cobertura especifica del area y no aparece evidencia nueva inicial de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 16:13:42Z: `RCDX-036 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/ruff_checks.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ruff_checks.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py` pasa (`18 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/quality_gate_components/toolchain.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` confirma `1 file would be reformatted` y `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`13 passed`), por lo que se materializa `RCDX-037 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/toolchain.py` como primera `TODO` no bloqueada.

- 2026-03-27 16:12:03Z: `RCDX-036 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/ruff_checks.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ruff_checks.py` mantiene una unica deuda de formato acotada a lineas en blanco sobrantes y a `_construir_comandos_ruff_loteados(...)`; `tests/test_quality_gate_ruff.py` y `tests/test_quality_gate_ruff_batching.py` siguen identificados como cobertura especifica del area y no aparece evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 15:53:14Z: `RCDX-035 - Alinear tests/test_toolchain_diagnostico.py con el interprete esperado por plataforma` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py` pasa (`6 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`7 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`31 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla de la suite corregida y ahora aborta por deuda real de formato en `scripts/quality_gate_components/ruff_checks.py` y `scripts/quality_gate_components/toolchain.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ruff_checks.py` y `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` confirman `1 file would be reformatted` en cada archivo, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py` pasa (`18 passed`), por lo que se materializa `RCDX-036 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/ruff_checks.py` como primera `TODO` no bloqueada y se deja `scripts/quality_gate_components/toolchain.py` para la siguiente ejecucion atomica.

- 2026-03-27 15:50:18Z: `RCDX-035 - Alinear tests/test_toolchain_diagnostico.py con el interprete esperado por plataforma` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py` reproduce un unico fallo en `test_cargar_toolchain_esperado_lee_versiones_desde_lock`, cuya asercion todavia exige `.venv/bin/python` aunque `scripts/quality_gate_components/toolchain.py` resuelve `.venv/Scripts/python.exe` en Windows; `tests/test_entorno_python.py` y `tests/test_gate_pr.py` siguen identificados como cobertura especifica complementaria del area y no aparece evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 15:34:14Z: `RCDX-034 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/ejecucion_canonica.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ejecucion_canonica.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` pasa (`14 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/quality_gate_components/ruff_checks.py` y `scripts/quality_gate_components/toolchain.py`. La prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` falla en `test_cargar_toolchain_esperado_lee_versiones_desde_lock`, mientras la inspeccion estatica de `tests/test_toolchain_diagnostico.py` y `scripts/quality_gate_components/toolchain.py` confirma que la suite todavia espera `.venv/bin/python` aunque `cargar_interprete_esperado(...)` resuelve `.venv/Scripts/python.exe` en Windows, por lo que se materializa `RCDX-035 - Alinear tests/test_toolchain_diagnostico.py con el interprete esperado por plataforma` como primera `TODO` no bloqueada.

- 2026-03-27 15:24:34Z: `RCDX-034 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/ejecucion_canonica.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ejecucion_canonica.py` mantiene una unica deuda de formato acotada a lineas en blanco sobrantes y a la firma de `reejecutar_en_python_objetivo(...)`, `tests/test_ejecucion_canonica.py` junto con `tests/test_gate_rapido.py` y `tests/test_gate_operational_contract_smoke.py` siguen identificados como cobertura especifica del area y no aparece evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 15:14:14Z: `RCDX-033 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/contrato_reason_codes_doc.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/contrato_reason_codes_doc.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py` pasa (`9 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/quality_gate_components/ejecucion_canonica.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ejecucion_canonica.py` confirma `1 file would be reformatted` y `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` pasa (`14 passed`), por lo que se materializa `RCDX-034 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/ejecucion_canonica.py` como primera `TODO` no bloqueada.

- 2026-03-27 15:12:06Z: `RCDX-033 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/contrato_reason_codes_doc.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/contrato_reason_codes_doc.py` mantiene una unica deuda de formato acotada al parser documental y `tests/test_gate_reason_codes_docs_sync.py` junto con `tests/test_quality_gate_reason_codes_doc_check.py` siguen identificados como cobertura especifica del area sin evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 14:54:48Z: `RCDX-032 - Alinear tests/test_ejecucion_canonica.py con el interprete esperado por plataforma` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py` pasa (`6 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` pasa (`8 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla de la suite corregida y ahora aborta por deuda real de formato en `scripts/quality_gate_components/contrato_reason_codes_doc.py` y `scripts/quality_gate_components/ejecucion_canonica.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/contrato_reason_codes_doc.py` y `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ejecucion_canonica.py` confirman `1 file would be reformatted` en cada archivo, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py` pasa (`9 passed`), por lo que se materializa `RCDX-033 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/contrato_reason_codes_doc.py` como primera `TODO` no bloqueada y se deja `scripts/quality_gate_components/ejecucion_canonica.py` para la siguiente ejecucion atomica.

- 2026-03-27 14:51:33Z: `RCDX-032 - Alinear tests/test_ejecucion_canonica.py con el interprete esperado por plataforma` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `tests/test_ejecucion_canonica.py` mantiene dos aserciones acopladas a `.venv/bin/python` mientras `scripts/quality_gate_components/toolchain.py` resuelve `.venv/Scripts/python.exe` en Windows, la inspeccion de `scripts/quality_gate_components/ejecucion_canonica.py` confirma que la logica productiva sigue alineada con ese helper canonico y no aparece evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 14:35:09Z: `RCDX-031 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/bloqueo_operativo.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/bloqueo_operativo.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_pr.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` pasa (`13 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/quality_gate_components/contrato_reason_codes_doc.py` y `scripts/quality_gate_components/ejecucion_canonica.py`. La prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` falla en `test_resolver_ejecucion_canonica_reejecuta_con_venv_repo` y `test_resolver_ejecucion_canonica_bloquea_si_python_repo_no_es_ejecutable`, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py` pasa (`9 passed`) y la inspeccion estatica de `tests/test_ejecucion_canonica.py`, `scripts/quality_gate_components/ejecucion_canonica.py` y `scripts/quality_gate_components/toolchain.py` confirma que la suite hardcodea `.venv/bin/python` aunque el helper canonico resuelve `.venv/Scripts/python.exe` en Windows, por lo que se materializa `RCDX-032 - Alinear tests/test_ejecucion_canonica.py con el interprete esperado por plataforma` como primera `TODO` no bloqueada.

- 2026-03-27 14:32:27Z: `RCDX-031 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/bloqueo_operativo.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/bloqueo_operativo.py` mantiene una unica deuda de formato acotada al `sys.stderr.write(...)` de `validaciones_no_ejecutadas` dentro de `reportar_bloqueo_operativo_doctor`, la inspeccion de `tests/test_gate_pr.py`, `tests/test_gate_rapido.py` y `tests/test_gate_operational_contract_smoke.py` deja identificada la cobertura especifica del area y no aparece evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 14:14:05Z: `RCDX-030 - Corregir el formateo Ruff pendiente en scripts/gate_pr.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/gate_pr.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_pr.py tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py` pasa (`14 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `scripts/quality_gate_components/bloqueo_operativo.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/bloqueo_operativo.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a colapsar en una sola linea el `sys.stderr.write(...)` de `validaciones_no_ejecutadas` dentro de `reportar_bloqueo_operativo_doctor`, y la inspeccion de `tests/test_gate_pr.py`, `tests/test_gate_rapido.py` y `tests/test_gate_operational_contract_smoke.py` identifica la cobertura especifica del area, por lo que se materializa `RCDX-031 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/bloqueo_operativo.py` como primera `TODO` no bloqueada.

- 2026-03-27 14:11:38Z: `RCDX-030 - Corregir el formateo Ruff pendiente en scripts/gate_pr.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m ruff format --check scripts/gate_pr.py` mantiene una unica deuda de formato acotada a `validar_contrato_reason_codes_doc`, la inspeccion de `tests/test_gate_pr.py`, `tests/test_gate_reason_codes_docs_sync.py` y `tests/test_quality_gate_reason_codes_doc_check.py` deja identificada la cobertura especifica del area y no aparece evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 13:53:22Z: `RCDX-029 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/shared/contexto_tabla.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/shared/contexto_tabla.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py` pasa (`2 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py` pasa (`3 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `scripts/gate_pr.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/gate_pr.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a colapsar en una sola linea el `raise ErrorContratoReasonCodesDoc(...)` dentro de `validar_contrato_reason_codes_doc`, y la inspeccion de `tests/test_gate_pr.py`, `tests/test_gate_reason_codes_docs_sync.py` y `tests/test_quality_gate_reason_codes_doc_check.py` identifica la cobertura especifica del area, por lo que se materializa `RCDX-030 - Corregir el formateo Ruff pendiente en scripts/gate_pr.py` como primera `TODO` no bloqueada.

- 2026-03-27 13:50:00Z: `RCDX-029 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/shared/contexto_tabla.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m ruff format --diff clinicdesk/app/pages/shared/contexto_tabla.py` mantiene una unica deuda de formato acotada al import largo inicial y `tests/ui/test_contexto_tabla.py` junto con `tests/ui/test_contexto_tabla_puro.py` siguen identificados en verde como cobertura especifica del contrato del area, sin evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 13:33:18Z: `RCDX-028 - Alinear tests/ui/test_contexto_tabla.py con el contrato visible de restaurar_contexto_tabla` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py` pasa (`2 passed`) tras validar el scroll restaurado contra el valor realmente capturado por la tabla visible, `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py` pasa (`3 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del area y ahora aborta por una deuda real de formato en `clinicdesk/app/pages/shared/contexto_tabla.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/shared/contexto_tabla.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a partir en varias lineas el import largo desde `clinicdesk.app.ui.ux.contexto_tabla`, por lo que se materializa `RCDX-029 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/shared/contexto_tabla.py` como primera `TODO` no bloqueada.

- 2026-03-27 13:31:35Z: `RCDX-028 - Alinear tests/ui/test_contexto_tabla.py con el contrato visible de restaurar_contexto_tabla` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py` mantiene reproducida la regresion al exigir `tabla.verticalScrollBar().value() == 7` sin garantizar ese rango en la tabla visible, `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py` sigue cubriendo el contrato puro en verde y no aparece evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 13:14:04Z: `RCDX-027 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/prediccion_ausencias/page.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/prediccion_ausencias/page.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_estabilidad.py` pasa (`9 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/pages/shared/contexto_tabla.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/shared/contexto_tabla.py` confirma `1 file would be reformatted`, pero la prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py` falla en `test_contexto_tabla_restaurar_seleccion_y_scroll` al exigir `tabla.verticalScrollBar().value() == 7` cuando una sonda local con la tabla visible devuelve `scroll_max 1`, `scroll_actual 1` y `scroll_capturado 1`; `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py` pasa, por lo que se materializa `RCDX-028 - Alinear tests/ui/test_contexto_tabla.py con el contrato visible de restaurar_contexto_tabla` como primera `TODO` no bloqueada.

- 2026-03-27 13:11:43Z: `RCDX-027 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/prediccion_ausencias/page.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/prediccion_ausencias/page.py` mantiene una unica deuda de formato acotada a `setText(...)` y al `contexto` de `_registrar_telemetria_monitor_ml`, `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_estabilidad.py` sigue en verde (`9 passed`) y no aparece evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 13:53:25Z: `RCDX-026 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py` pasa (`4 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/pages/prediccion_ausencias/page.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/prediccion_ausencias/page.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a una llamada larga a `setText(...)` y a la construccion de `contexto` en `_registrar_telemetria_monitor_ml`, y `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_estabilidad.py` pasa, por lo que se materializa `RCDX-027 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/prediccion_ausencias/page.py` como primera `TODO` no bloqueada.

- 2026-03-27 13:51:32Z: `RCDX-026 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py` sigue en verde (`4 passed`) y `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` mantiene un unico bloqueo de formato acotado al dialogo, sin evidencia nueva de bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad.

- 2026-03-27 12:37:06Z: `RCDX-025 - Alinear tests/ui/test_paciente_form_dialog.py con el contrato visible de PacienteFormDialog` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py` pasa tras mostrar el dialogo, validar foco/visibilidad con la ventana visible y cerrarlo explicitamente para evitar que el teardown abra el modal de cambios sin guardar; `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del bloqueo del area y ahora aborta por una deuda real de formato en `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` confirma `1 file would be reformatted`, por lo que se materializa `RCDX-026 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` como primera `TODO` no bloqueada.

- 2026-03-27 12:31:33Z: `RCDX-025 - Alinear tests/ui/test_paciente_form_dialog.py con el contrato visible de PacienteFormDialog` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `tests/ui/test_paciente_form_dialog.py` mantiene reproducida la regresion al validar `isVisible()` y `hasFocus()` sin mostrar el dialogo, y la sonda previa del formulario visible sigue acotando el ajuste al wiring de la suite UI.

- 2026-03-27 12:13:11Z: `RCDX-024 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/citas/logging_payloads.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/logging_payloads.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_citas_calendario_logging.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` confirma `1 file would be reformatted`, `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py` falla en `test_paciente_form_validacion_inline_y_cta` y `test_paciente_form_foco_en_primer_error`, y una sonda local con el dialogo mostrado devuelve `email_visible True` y `documento_focus True`, por lo que la prioridad real pasa a alinear esa suite con el contrato visible antes de retomar la deuda de Ruff en `paciente_form.py`. Se materializa `RCDX-025 - Alinear tests/ui/test_paciente_form_dialog.py con el contrato visible de PacienteFormDialog` como primera `TODO` no bloqueada.

- 2026-03-27 12:10:58Z: `RCDX-024 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/citas/logging_payloads.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --diff clinicdesk/app/pages/citas/logging_payloads.py` sigue acotando la incidencia a la firma larga de `payload_log_error_calendario(...)` y `tests/test_citas_calendario_logging.py` mantiene cubierto el contrato del payload de logging.

- 2026-03-27 12:57:29Z: `RCDX-023 - Restablecer el foco del primer error en clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_cita_form_dialog.py` pasa tras mostrar el dialogo, mover el foco a `ed_fin` y reenviar el formulario invalido, confirmando que el contrato real de foco se valida con el dialogo visible; `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del bloqueo actual y ahora aborta por una deuda real de formato en `clinicdesk/app/pages/citas/logging_payloads.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/logging_payloads.py` confirma `1 file would be reformatted` y `.\.venv\Scripts\python.exe -m pytest -q tests/test_citas_calendario_logging.py` pasa, por lo que se materializa `RCDX-024 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/citas/logging_payloads.py` como primera `TODO` no bloqueada.

- 2026-03-27 12:51:43Z: `RCDX-023 - Restablecer el foco del primer error en clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `tests/ui/test_cita_form_dialog.py` mantiene reproducida la regresion de foco en `test_cita_form_foco_en_primer_error` y `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` sigue siendo la unica zona requerida para corregirla.

- 2026-03-27 11:33:25Z: `RCDX-022 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` queda en verde y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_cita_form_dialog.py` falla en `test_cita_form_foco_en_primer_error` porque `dialogo.ed_inicio.hasFocus()` queda en `False` tras `dialogo._on_ok()`. `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y tambien revela una deuda real de formato en `clinicdesk/app/pages/citas/logging_payloads.py`, pero por prioridad contractual el test roto del area pasa delante de la siguiente incidencia de Ruff, por lo que se materializa `RCDX-023 - Restablecer el foco del primer error en clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` como primera `TODO` no bloqueada.

- 2026-03-27 11:31:08Z: `RCDX-022 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` sigue reproduciendo solo deuda de formato en el dialogo y `tests/ui/test_cita_form_dialog.py` mantiene cubierto el area afectada.

- 2026-03-27 11:14:33Z: `RCDX-021 - Corregir el formateo Ruff pendiente en clinicdesk/app/i18n_catalogos/ux.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_i18n_catalog.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en un lote que incluye `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` y `clinicdesk/app/pages/citas/logging_payloads.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a partir en varias lineas dos llamadas largas a `form.addRow(...)`, `tests/ui/test_cita_form_dialog.py` queda identificado como suite especifica del area afectada y `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/logging_payloads.py` confirma la deuda residual del segundo archivo del lote, por lo que se materializa `RCDX-022 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` como primera `TODO` no bloqueada.

- 2026-03-27 11:11:56Z: `RCDX-021 - Corregir el formateo Ruff pendiente en clinicdesk/app/i18n_catalogos/ux.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py` sigue reproduciendo solo deuda de formato en el catalogo y `tests/test_i18n_catalog.py` mantiene cubierto el area afectada.

- 2026-03-27 10:53:09Z: `RCDX-020 - Corregir el formateo Ruff pendiente en clinicdesk/app/i18n_catalogos/pred.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/pred.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_i18n_catalog.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/i18n_catalogos/ux.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py` confirma `1 file would be reformatted` y el diff de Ruff acota el cambio a eliminar dos lineas en blanco sobrantes entre grupos de claves del catalogo, por lo que se materializa `RCDX-021 - Corregir el formateo Ruff pendiente en clinicdesk/app/i18n_catalogos/ux.py` como primera `TODO` no bloqueada.

- 2026-03-27 10:51:39Z: `RCDX-020 - Corregir el formateo Ruff pendiente en clinicdesk/app/i18n_catalogos/pred.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/pred.py` sigue reproduciendo solo deuda de formato en el catalogo y `tests/test_i18n_catalog.py` mantiene cubierto el area afectada.

- 2026-03-27 10:34:30Z: `RCDX-019 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_seguimiento_operativo_ml_service.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en un lote que incluye `clinicdesk/app/i18n_catalogos/pred.py` y `clinicdesk/app/i18n_catalogos/ux.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/pred.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a eliminar lineas en blanco sobrantes y agregar comas finales faltantes dentro del catalogo, `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py` confirma la deuda residual del segundo archivo del lote y `tests/test_i18n_catalog.py` queda identificado como suite especifica del area afectada, por lo que se materializa `RCDX-020 - Corregir el formateo Ruff pendiente en clinicdesk/app/i18n_catalogos/pred.py` como primera `TODO` no bloqueada.

- 2026-03-27 10:32:22Z: `RCDX-019 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` sigue reproduciendo un unico ajuste de formato pendiente y `tests/test_seguimiento_operativo_ml_service.py` mantiene cubierto el area funcional afectada.

- 2026-03-27 10:18:54Z: `RCDX-018 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/ml_playbooks_service.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_playbooks_service.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_ml_playbooks_service.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/application/services/seguimiento_operativo_ml_service.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a eliminar una linea en blanco final sobrante y `tests/test_seguimiento_operativo_ml_service.py` queda identificado como suite especifica del area afectada, por lo que se materializa `RCDX-019 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` como primera `TODO` no bloqueada.

- 2026-03-27 10:16:42Z: `RCDX-018 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/ml_playbooks_service.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_playbooks_service.py` sigue reproduciendo un unico ajuste de formato pendiente y `tests/test_ml_playbooks_service.py` mantiene cubierto el area funcional afectada.

- 2026-03-27 09:02:33Z: `RCDX-017 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/ml_centro_guiado_service.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_centro_guiado_service.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_ml_centro_guiado_service.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/application/services/ml_playbooks_service.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_playbooks_service.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a partir la firma larga de `_pasos_playbook(...)` y `tests/test_ml_playbooks_service.py` queda identificado como suite especifica del area afectada, por lo que se materializa `RCDX-018 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/ml_playbooks_service.py` como primera `TODO` no bloqueada.

- 2026-03-27 09:01:16Z: `RCDX-017 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/ml_centro_guiado_service.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_centro_guiado_service.py` sigue reproduciendo un unico ajuste de formato pendiente y `tests/test_ml_centro_guiado_service.py` mantiene cubierto el area funcional afectada.

- 2026-03-27 08:03:17Z: `RCDX-016 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/demo_ml_facade.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/demo_ml_facade.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_demo_ml_facade.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en un lote que incluye `clinicdesk/app/application/services/ml_centro_guiado_service.py` y `clinicdesk/app/application/services/ml_playbooks_service.py`. `.\.venv\Scripts\python.exe -m ruff format --check` confirma `1 file would be reformatted` en ambos archivos; para mantener la disciplina de una sola incidencia por ejecucion, se materializa `RCDX-017 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/ml_centro_guiado_service.py` como primera `TODO` no bloqueada.

- 2026-03-27 08:01:37Z: `RCDX-016 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/demo_ml_facade.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/demo_ml_facade.py` sigue reproduciendo un unico ajuste de formato pendiente y `tests/test_demo_ml_facade.py` mantiene cubierto el area funcional afectada.

- 2026-03-27 07:03:21Z: `RCDX-015 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/seguros/economia_poliza.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/seguros/economia_poliza.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/application/seguros/test_economia_poliza_service.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y sigue bloqueado por una deuda real de formato en `clinicdesk/app/application/services/demo_ml_facade.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/demo_ml_facade.py` confirma `1 file would be reformatted` y el diff de Ruff acota el cambio a eliminar una linea en blanco sobrante antes de `list_dataset_versions`, por lo que se materializa `RCDX-016 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/demo_ml_facade.py` como primera `TODO` no bloqueada.

- 2026-03-27 06:18:30Z: `RCDX-015 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/seguros/economia_poliza.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/seguros/economia_poliza.py` sigue reproduciendo un unico ajuste de formato pendiente y `tests/application/seguros/test_economia_poliza_service.py` mantiene cubierto el area funcional afectada.

- 2026-03-27 06:02:40Z: `RCDX-014 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/seguros/__init__.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/seguros/__init__.py` queda en verde, `python -m scripts.gate_rapido` devuelve `rc=0` y `python -m scripts.gate_pr` avanza mas alla del archivo objetivo; sin embargo, el gate completo sigue bloqueado por una deuda real de formato en `clinicdesk/app/application/seguros/economia_poliza.py`. Se materializa `RCDX-015 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/seguros/economia_poliza.py` como primera `TODO` no bloqueada.

- 2026-03-27 05:14:00Z: `RCDX-014 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/seguros/__init__.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/seguros/__init__.py` sigue reproduciendo un unico ajuste de formato pendiente en ese archivo.

- 2026-03-27 05:04:14Z: `RCDX-013 - Corregir el formateo Ruff pendiente en interpretacion_ml_humana.py` queda en `BLOCKED`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/ml/interpretacion_ml_humana.py` queda en verde, `python -m scripts.gate_rapido` devuelve `rc=0` y `python -m scripts.gate_pr` avanza mas alla del archivo objetivo; sin embargo, el gate completo sigue bloqueado por una deuda real de formato en un archivo distinto: `clinicdesk/app/application/seguros/__init__.py`. Se materializa `RCDX-014 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/seguros/__init__.py` como primera `TODO` no bloqueada.

- 2026-03-27 04:24:00Z: `RCDX-013 - Corregir el formateo Ruff pendiente en interpretacion_ml_humana.py` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; el bloqueo vigente de `python -m scripts.gate_pr` sigue acotado a la deuda de `ruff format --check` en `clinicdesk/app/application/ml/interpretacion_ml_humana.py`.

- 2026-03-27 04:04:35Z: `RCDX-012 â€” Acotar los lotes de Ruff format-check al limite operativo` queda en `BLOCKED`. La regresion especifica queda en verde con `.\.venv\Scripts\python.exe -m pytest -q tests/test_ruff_targets.py tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py tests/test_gate_pr.py` y `python -m scripts.gate_rapido` devolvio `rc=0`; ademas `python -m scripts.gate_pr` mantiene corregido el `WinError 206` y ya acota `ruff format --check` a lotes de `10` archivos, pero ahora aborta por deuda real de formato en un unico archivo: `clinicdesk/app/application/ml/interpretacion_ml_humana.py`. Se materializa `RCDX-013 â€” Corregir el formateo Ruff pendiente en interpretacion_ml_humana.py` como primera `TODO` no bloqueada.

- 2026-03-27 04:01:24Z: `RCDX-012 â€” Acotar los lotes de Ruff format-check al limite operativo` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; el bloqueo vigente de `python -m scripts.gate_pr` sigue acotado a que `ruff format --check` reporta `14 files would be reformatted` en el primer lote, por encima del limite operativo de `10` archivos por ejecucion.

- 2026-03-27 04:08:47Z: `RCDX-011 — Acotar la invocacion de Ruff del gate completo en Windows` queda en `BLOCKED`. La regresion especifica queda en verde con `.\.venv\Scripts\python.exe -m pytest -q tests/test_ruff_targets.py tests/test_quality_gate_ruff.py tests/test_gate_pr.py` y `python -m scripts.gate_rapido` devolvio `rc=0`; ademas `python -m scripts.gate_pr` ya ejecuta Ruff por lotes y evita el `WinError 206`, pero ahora aborta por un bloqueo real de formateo: `ruff format --check` reporta `14 files would be reformatted` en el primer lote. Revalidacion final 2026-03-27 04:13:09Z: tras actualizar roadmap y bitacora, `python -m scripts.gate_rapido` siguio en `rc=0` y `python -m scripts.gate_pr` repitio el mismo bloqueo de formato en `14` archivos. Como corregir esos `14` archivos en una sola ejecucion excederia el limite operativo de `10` archivos modificados por run, se materializa `RCDX-012 — Acotar los lotes de Ruff format-check al limite operativo` como primera `TODO` no bloqueada.
- 2026-03-27 02:28:00Z: `RCDX-011 — Acotar la invocacion de Ruff del gate completo en Windows` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque no se detecto antes ningun bug critico, test roto, error de ejecucion de producto ni bloqueo de entorno que reordene la prioridad; la medicion local confirma `995` targets Python versionados y una linea estimada de `47606` caracteres para `ruff check`, suficiente para reproducir el `WinError 206` en Windows sin ampliar el alcance mas alla del quality gate.
- 2026-03-27 02:03:43Z: `RCDX-010 — Excluir .venv del guardarrail PII/logging del gate completo` queda en `BLOCKED`. La regresion especifica queda en verde con `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_security.py tests/test_gate_pr.py` y `python -m scripts.gate_rapido` devolvio `rc=0`; ademas `python -m scripts.gate_pr` ya supera `scripts.quality_gate_components.pii_guardrail`, `pip-audit` y `secrets_scan`, pero aborta despues en `scripts.quality_gate_components.ruff_checks` con `FileNotFoundError: [WinError 206] El nombre del archivo o la extension es demasiado largo` al ejecutar `check_command = [sys.executable, "-m", "ruff", "check", *python_targets]`. Se materializa `RCDX-011 — Acotar la invocacion de Ruff del gate completo en Windows` como primera `TODO` no bloqueada.
- 2026-03-27 02:01:50Z: `RCDX-010 — Excluir .venv del guardarrail PII/logging del gate completo` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `python -m scripts.gate_pr` continua bloqueado por falsos positivos del guardarrail PII/logging sobre `.\.venv\Lib\site-packages\**\*.py`; no se detecto antes ningun bug critico, test roto o bloqueo de producto que reordene la prioridad.
- 2026-03-27 01:09:18Z: `RCDX-009 — Resolver hallazgos activos de pip-audit en el gate completo` queda en `BLOCKED`. La regresion especifica queda en verde con `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_security.py tests/test_gate_pr.py` y `python -m scripts.gate_rapido` devolvio `rc=0`; ademas `python -m scripts.gate_pr` ya avanza mas alla de `pip-audit` y registra `pip-audit solo reporto vulnerabilidades allowlisted`, pero falla despues porque `scripts/quality_gate_components/pii_guardrail.py` escanea `.\.venv\Lib\site-packages\**\*.py` y reporta claves `nif` de terceros. Se materializa `RCDX-010 — Excluir .venv del guardarrail PII/logging del gate completo` como primera `TODO` no bloqueada.
- 2026-03-27 01:02:21Z: `RCDX-009 — Resolver hallazgos activos de pip-audit en el gate completo` pasa a `WIP`. Sigue siendo la primera tarea elegible real porque `python -m scripts.gate_pr` permanece bloqueado en el paso `pip-audit`; la inspección del lock y del entorno confirma que `pip 25.3` tiene fix disponible (`26.0+`), mientras `pygments 2.19.2` sigue siendo la última versión publicada y no ofrece fix reproducible inmediato, por lo que la prioridad vigente es un ajuste mínimo de tooling/allowlist y no una feature de producto.
- 2026-03-27 00:03:38Z: `RCDX-008 — Excluir .venv del check no-print del gate completo` queda en `BLOCKED`. La regresión específica quedó en verde con `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_security.py tests/test_gate_pr.py` y `python -m scripts.gate_rapido` devolvió `rc=0`; además `python -m scripts.gate_pr` ya no falla por `print` dentro de `.\.venv`, pero avanza hasta `pip-audit` y aborta por vulnerabilidades no allowlisted (`GHSA-6vgw-5pg2-w6jp` en `pip 25.3` y `GHSA-5239-wwwm-4pmq` en `pygments 2.19.2`). Se materializa `RCDX-009 — Resolver hallazgos activos de pip-audit en el gate completo` como primera `TODO` no bloqueada.
- 2026-03-27 00:01:18Z: `RCDX-008 — Excluir .venv del check no-print del gate completo` pasa a `WIP`. Sigue siendo la primera tarea elegible y la prioridad real vigente porque `python -m scripts.gate_pr` continúa bloqueado por un falso positivo del guardarraíl `check_no_print_calls(...)` sobre `.\.venv\Lib\site-packages\**\*.py`; no se detectó un bug crítico anterior que reordene el backlog.
- 2026-03-26 23:06:20Z: `RCDX-007 — Retirar o alinear launcher Windows legado` vuelve a `BLOCKED`. La validación específica ya quedó en verde con `.\.venv\Scripts\python.exe -m pytest -q tests/guardrails/test_saneamiento_legacy_repo.py tests/test_build_release.py` y `python -m scripts.gate_rapido` también pasa tras recuperar el toolchain local, pero `python -m scripts.gate_pr` falla por un guardarraíl roto: `scripts/quality_gate_components/basic_repo_checks.py` inspecciona `.\.venv\Lib\site-packages\**\*.py` en `check_no_print_calls(...)` y reporta `print` de dependencias instaladas. Se materializa `RCDX-008 — Excluir .venv del check no-print del gate completo` como primera `TODO` no bloqueada.
- 2026-03-26 23:03:00Z: backlog operativo reabierto. `RCDX-007 — Retirar o alinear launcher Windows legado` pasa a `WIP` porque el bloqueo de entorno previo dejó de ser concluyente en este worktree: `.\.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip` vuelve a funcionar y la sonda `python -c "import tempfile, pathlib; d=tempfile.TemporaryDirectory(dir='.tmp'); ..."` completa con `ok`, por lo que la validación pendiente puede reintentarse localmente.
- 2026-03-26 22:03:45Z: `RCDX-007 - Retirar o alinear launcher Windows legado` queda en `BLOCKED`. `launch.bat` ya delega a `launcher.bat` y el guardarrail evita reintroducir branding legado o referencias a `main.py`, pero los checks obligatorios no pudieron quedar en verde: `pytest -q tests/guardrails/test_saneamiento_legacy_repo.py tests/test_build_release.py` falla porque `pytest` no esta disponible en PATH y `python -m scripts.gate_rapido` aborta con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`.
- 2026-03-26 22:03:54Z: no existe ninguna tarea `TODO` no bloqueada. `RCDX-007 - Retirar o alinear launcher Windows legado` sigue en `BLOCKED`: `launch.bat` y el guardarrail permanecen corregidos en el worktree, pero `.\.venv\Scripts\python.exe -m pytest --version` falla con `No module named pytest` y `python -m scripts.gate_rapido` vuelve a abortar con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`. La nota `WIP` residual queda superada y el backlog operativo vuelve a quedar sin tarea seleccionable.

- 2026-03-26 21:36:42Z: backlog operativo reabierto. La primera tarea `TODO` no bloqueada es `RCDX-007 — Retirar o alinear launcher Windows legado`, porque `launch.bat` sigue versionado en la raíz, exige `main.py` inexistente y conserva branding `Horas Sindicales`, mientras los entrypoints soportados del repo son `scripts/run_app.py`, `START_APP.bat` y `launcher.bat`.

## Tareas

### RCDX-001 — Fundar contrato operativo de automations
- **estado**: DONE
- **objetivo**: Establecer contrato permanente para agentes, roadmap operativo y bitácora append-only.
- **alcance permitido**:
  - actualizar `AGENTS.md` como contrato operativo del repo,
  - crear `docs/roadmap_codex.md`,
  - crear `docs/bitacora_codex.md`,
  - aclarar relación con `docs/roadmap_codex_automation.md`.
- **fuera de alcance**:
  - cambios de lógica de negocio,
  - UI/infra/CI,
  - refactors funcionales.
- **archivos o zonas probables**:
  - `AGENTS.md`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
  - `docs/roadmap_codex_automation.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
  - verificación manual de no binarios en diff
- **criterios de cierre**:
  - contrato operativo explícito y ejecutable para Codex,
  - roadmap atómico listo para selección automática,
  - bitácora inicializada y append-only.
- **dependencias o bloqueo**: ninguna.

### RCDX-002 — Enlazar ejecución diaria con disciplina de una tarea
- **estado**: BLOCKED
- **objetivo**: Asegurar que cada run mantenga disciplina de una única tarea y sin expansión de alcance.
- **alcance permitido**:
  - reforzar texto operativo en docs si hay ambigüedad residual,
  - verificar consistencia entre `AGENTS.md`, roadmap y bitácora.
- **fuera de alcance**:
  - cambios de producto,
  - cambios de scripts del gate.
- **archivos o zonas probables**:
  - `AGENTS.md`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
- **criterios de cierre**:
  - no hay contradicciones entre contrato y operación diaria,
  - queda explícito cómo proceder ante bloqueo y parada,
  - queda explícita la regla `DONE` vs `BLOCKED` cuando no se pueden completar checks obligatorios,
  - roadmap y bitácora documentan `N/A por bloqueo operativo` para metadata de commit/PR cuando corresponda.
- **dependencias o bloqueo**: RCDX-001 DONE. Revalidación 2026-03-26: persiste bloqueo operativo de validación con `reason_code=DEPENDENCIAS_FALTANTES` en `python -m scripts.doctor_entorno_calidad` y `rc=20` en `python -m scripts.gate_rapido`; `python scripts/setup.py` no logra instalar dependencias runtime por proxy/red (`Tunnel connection failed: 403 Forbidden` y `No matching distribution found for PySide6==6.8.3`) sin wheelhouse local, por lo que no se puede alinear el toolchain en este entorno.

### RCDX-003 — Mantener trazabilidad entre roadmap operativo e histórico
- **estado**: DONE
- **objetivo**: Evitar deriva entre roadmap operativo actual e histórico narrativo de automatizaciones.
- **alcance permitido**:
  - añadir notas de enlace cruzado y reglas de actualización mínima.
- **fuera de alcance**:
  - reescritura histórica completa,
  - compactación destructiva del historial.
- **archivos o zonas probables**:
  - `docs/roadmap_codex.md`
  - `docs/roadmap_codex_automation.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
- **criterios de cierre**:
  - relación histórico↔operativo inequívoca y estable.
- **dependencias o bloqueo**: RCDX-001 DONE.

### RCDX-004 — Estandarizar plantilla de cierre en bitácora
- **estado**: BLOCKED
- **objetivo**: Consolidar formato de evidencia para cierres de ejecución (checks, decisión, siguiente paso).
- **alcance permitido**:
  - ajustar únicamente estructura documental de `docs/bitacora_codex.md`.
- **fuera de alcance**:
  - cambios de scripts,
  - cambios funcionales de producto.
- **archivos o zonas probables**:
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
- **criterios de cierre**:
  - plantilla clara, reutilizable y append-only.
- **dependencias o bloqueo**: RCDX-001 DONE. Revalidación 2026-03-26: `python -m scripts.gate_rapido` aborta con `rc=20`/`reason_code=VENV_REPO_NO_DISPONIBLE`; `python scripts/setup.py` y `python -m venv .venv` fallan al ejecutar `ensurepip`; además `python -c "import tempfile, pathlib; d=tempfile.TemporaryDirectory(dir='.tmp'); p=pathlib.Path(d.name)/'probe.txt'; p.write_text('ok', encoding='utf-8')"` reproduce `PermissionError [Errno 13]`/`WinError 5` incluso dentro de `.tmp` del worktree, por lo que `.venv` queda parcial sin `pip` y no se puede instalar el toolchain obligatorio (`ruff`, `pytest`, `mypy`, `pip-audit`) ni completar la validación.

### RCDX-005 — Registrar backlog sin tarea seleccionable
- **estado**: BLOCKED
- **objetivo**: Hacer explícito el bloqueo contractual cuando el roadmap operativo queda sin ninguna tarea `TODO` elegible para automations.
- **alcance permitido**:
  - documentar el agotamiento o bloqueo total del backlog seleccionable,
  - exigir definición de la siguiente tarea priorizada o cierre explícito del backlog,
  - mantener trazabilidad entre roadmap y bitácora sin inventar trabajo funcional.
- **fuera de alcance**:
  - crear prioridad funcional nueva sin decisión humana,
  - ejecutar cambios de producto sin tarea seleccionable,
  - reordenar tareas ya registradas.
- **archivos o zonas probables**:
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
- **criterios de cierre**:
  - existe al menos una tarea `TODO` no bloqueada en el roadmap, o
  - se declara explícitamente que el backlog operativo queda cerrado.
- **dependencias o bloqueo**: El roadmap vigente solo contiene `RCDX-001` DONE, `RCDX-002` BLOCKED, `RCDX-003` DONE y `RCDX-004` BLOCKED; no existe ninguna entrada `TODO` seleccionable. Revalidación 2026-03-26 16:02Z: la ejecución sigue en la rama aislada `codex/radar-inspector-20260326` y `python -m scripts.gate_rapido` aborta con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES` porque faltan `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv`; además `wheelhouse/` sigue ausente, por lo que tampoco hay validación automática disponible para promover este cierre documental a `DONE`. Revalidación 2026-03-26 18:02Z: persiste la misma ausencia de tarea `TODO` elegible y el gate vuelve a abortar en preflight con `reason_code=DEPENDENCIAS_FALTANTES`; el doctor confirma que el intérprete del repo sí es utilizable, pero siguen faltando `ruff`, `pytest`, `mypy` y `pip-audit` y no existe `wheelhouse/`, por lo que continúa el doble bloqueo de gobernanza y toolchain. Revalidación 2026-03-26 18:02:28Z: la rama activa sigue siendo `codex/radar-inspector-20260326`, el selector continúa sin ninguna `TODO` elegible y `python -m scripts.gate_rapido` vuelve a abortar con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`; faltan `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv` y `wheelhouse/` permanece ausente, así que el bloqueo contractual y el del toolchain siguen sin cambios. Revalidación 2026-03-26 19:01:50Z: la ejecución permanece en la rama aislada `codex/radar-inspector-20260326`, `git status --short --untracked-files=no` solo muestra cambios documentales en `docs/roadmap_codex.md` y `docs/bitacora_codex.md`, el selector sigue sin ninguna `TODO` elegible y `python -m scripts.gate_rapido` vuelve a abortar con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`; el doctor confirma de nuevo que faltan `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv` y que `wheelhouse/` sigue ausente. Revalidación 2026-03-26 20:01:16Z: la ejecución sigue en la rama aislada `codex/radar-inspector-20260326`, `git status --short --untracked-files=no` estaba limpio antes de documentar, el selector continúa sin ninguna `TODO` elegible y `python -m scripts.gate_rapido` vuelve a abortar con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`; el doctor confirma otra vez que faltan `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv` y que `wheelhouse/` permanece ausente. Revalidación 2026-03-26 21:36:42Z: deja de aplicar el cierre total del backlog porque se detecta `launch.bat` versionado en la raíz como entrypoint Windows legado roto; el archivo exige `main.py` inexistente, ejecuta `main.py` y muestra `Launcher Horas Sindicales iniciado`, mientras `README.md`, `scripts/run_app.py`, `START_APP.bat` y `launcher.bat` ya apuntan al entrypoint real `clinicdesk.app.main`. Se materializa `RCDX-007` como primera `TODO` no bloqueada; `python -m scripts.gate_rapido` sigue abortando con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES` por ausencia de `ruff`, `pytest`, `mypy` y `pip-audit` en `.venv`. Revalidación 2026-03-26 22:03:54Z: tras quedar `RCDX-007` en `BLOCKED`, el backlog vuelve a quedarse sin ninguna `TODO` elegible; `.\.venv\Scripts\python.exe -m pytest --version` falla con `No module named pytest` y `python -m scripts.gate_rapido` sigue abortando con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`, así que el cierre contractual continúa bloqueado hasta restaurar el toolchain o priorizar una nueva tarea.

  Revalidacion 2026-03-27 20:14:14Z: el roadmap vuelve a estar sin ninguna tarea `TODO` ni `WIP` elegible; `python -m scripts.gate_rapido` ahora pasa (`rc=0`), pero `python -m scripts.gate_pr` aborta en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`. `git ls-files data` y `git status --short data` no listan esos archivos, asi que el bloqueo vigente proviene de SQLite locales ignorados del worktree y, por prohibicion contractual de tocar binarios en esta ejecucion, solo corresponde documentar el bloqueo y exigir un workspace limpio antes de reactivar el backlog.

  Revalidacion 2026-03-27 20:33:36Z: el backlog sigue sin ninguna tarea `TODO` ni `WIP` elegible y `python -m scripts.gate_rapido` vuelve a pasar (`rc=0`), por lo que no aparece evidencia nueva de bug critico ni de tests rotos que reordene prioridades. `python -m scripts.gate_pr` aborta otra vez en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`; `git ls-files data` y `git status --short data` siguen vacios, `git check-ignore -v` confirma `.gitignore:8:data/` y `Get-ChildItem data` muestra que son artefactos locales del worktree. Sin una `TODO` real y por prohibicion contractual de tocar binarios en esta ejecucion, solo corresponde documentar el bloqueo y exigir un workspace limpio antes de reactivar el backlog.

### RCDX-006 — Saneamiento contractual Bootstrap 1
- **estado**: BLOCKED
- **objetivo**: Verificar y corregir contradicciones mínimas entre contrato, roadmap, bitácora, gates canónicos y la variante real de arquitectura del repo para dejar el backlog listo para automations seguras.
- **alcance permitido**:
  - ajustar `AGENTS.md` para mapear Clean Architecture a `clinicdesk/app/domain`, `clinicdesk/app/application`, `clinicdesk/app/infrastructure`, `clinicdesk/app/ui` y `clinicdesk/app/pages`,
  - actualizar `docs/roadmap_codex.md` para reflejar esta priorización humana y el estado seleccionable real del backlog,
  - añadir evidencia append-only en `docs/bitacora_codex.md`,
  - tocar `docs/roadmap_codex_automation.md` solo si aparece una contradicción contractual estricta.
- **fuera de alcance**:
  - cambios de producto,
  - cambios de scripts, CI o dependencias,
  - refactors funcionales o de arquitectura ejecutable.
- **archivos o zonas probables**:
  - `AGENTS.md`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
  - `docs/roadmap_codex_automation.md`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
  - verificación manual de no binarios en diff
- **criterios de cierre**:
  - el contrato operativo referencia la variante real de capas del repo,
  - el roadmap deja explícito si existe tarea seleccionable o backlog cerrado,
  - la bitácora registra decisiones, checks y bloqueo real de entorno si aplica.
- **dependencias o bloqueo**: Priorización humana 2026-03-26: `BOOTSTRAP CONTRATO 1`. Revalidación 2026-03-26 20:11:48Z: `python -m scripts.gate_rapido` vuelve a abortar con `rc=20`/`reason_code=DEPENDENCIAS_FALTANTES`; el intérprete de `.venv` es utilizable, pero siguen ausentes `ruff`, `pytest`, `mypy` y `pip-audit`, `wheelhouse/` permanece ausente y el check obligatorio no queda en verde. La tarea debe cerrarse en `BLOCKED` y el backlog operativo vuelve a quedar cerrado hasta nueva priorización humana.

### RCDX-007 — Retirar o alinear launcher Windows legado
- **estado**: BLOCKED
- **objetivo**: Eliminar el entrypoint Windows versionado que hoy no puede arrancar la app y contradice el branding y los entrypoints soportados del repo.
- **alcance permitido**:
  - corregir `launch.bat` para que delegue al entrypoint real soportado o retirarlo si se confirma que es legado no soportado,
  - mantener consistencia mínima con `START_APP.bat`, `launcher.bat` y `README.md`,
  - añadir guardarraíl o verificación mínima si hace falta para evitar la reintroducción del launcher legado roto.
- **fuera de alcance**:
  - cambios de lógica de negocio o UI,
  - cambios de packaging/release más allá del launcher raíz,
  - cambios de CI, dependencias o setup.
- **archivos o zonas probables**:
  - `launch.bat`
  - `START_APP.bat`
  - `launcher.bat`
  - `README.md`
  - `tests/guardrails/test_saneamiento_legacy_repo.py`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
  - `pytest -q tests/guardrails/test_saneamiento_legacy_repo.py tests/test_build_release.py`
- **criterios de cierre**:
  - `launch.bat` deja de apuntar a `main.py` inexistente y ya no conserva branding ajeno,
  - los launchers Windows soportados quedan alineados con `clinicdesk.app.main` o `scripts/run_app.py`,
  - existe una protección mínima para que el launcher legado roto no reaparezca.
- **dependencias o bloqueo**: Evidencia 2026-03-26 21:36:42Z: `launch.bat` versionado en la raíz comprueba `main.py`, ejecuta `"%VENV_PY%" main.py` y muestra `Launcher Horas Sindicales iniciado`; `main.py` no existe en la raíz del repo y el README documenta `python scripts/run_app.py`, mientras `START_APP.bat` y `launcher.bat` sí delegan a `clinicdesk.app.main`. Revalidación 2026-03-26 23:03:00Z: `.\.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip` vuelve a instalar `pip` y la sonda de `tempfile` en `.tmp` completa con `ok`; se reactiva la validación local del launcher. Revalidación 2026-03-26 23:06:20Z: `python -m scripts.gate_pr` ya no cae por dependencias faltantes, pero aborta porque `check_no_print_calls(...)` recorre `.\.venv\Lib\site-packages\*.py` y reporta `print` de terceros, así que el cierre en `DONE` queda bloqueado por un bug del gate completo ajeno al launcher.

### RCDX-008 — Excluir `.venv` del check no-print del gate completo
- **estado**: BLOCKED
- **objetivo**: Evitar que el gate completo trate como código del repo los `print(...)` contenidos en dependencias instaladas dentro de `.venv`.
- **alcance permitido**:
  - corregir `scripts/quality_gate_components/basic_repo_checks.py` para que `check_no_print_calls(...)` respete `SCAN_EXCLUDE_DIRS` o reutilice el iterador ya filtrado,
  - añadir una regresión mínima en tests para congelar que `.venv` y otros directorios excluidos no se escanean en ese check,
  - mantener intacta la detección de `print(...)` en código propio del repositorio.
- **fuera de alcance**:
  - relajar la política `no print` sobre archivos del repo,
  - cambios funcionales de producto,
  - refactors amplios del quality gate.
- **archivos o zonas probables**:
  - `scripts/quality_gate_components/basic_repo_checks.py`
  - `tests/test_quality_gate_security.py`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_security.py tests/test_gate_pr.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `check_no_print_calls(...)` deja de inspeccionar `.venv` y demás directorios excluidos,
  - el guardarraíl sigue detectando `print(...)` en código propio no allowlisted,
  - `python -m scripts.gate_pr` deja de fallar por `print` de `site-packages`.
- **dependencias o bloqueo**: Evidencia 2026-03-26 23:06:20Z: `python -m scripts.gate_pr` falla tras recuperar toolchain local, y el log de `scripts.quality_gate_components.basic_repo_checks` enumera `print encontrado en .venv\\Lib\\site-packages\\...` porque `check_no_print_calls(...)` usa `root.rglob("*.py")` sin aplicar `SCAN_EXCLUDE_DIRS={".git", ".venv", "__pycache__", ".pytest_cache", "logs"}` ya definidas en `scripts/quality_gate_components/config.py`. Revalidación 2026-03-27 00:03:38Z: el guardarraíl ya respeta exclusiones, `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_security.py tests/test_gate_pr.py` queda en verde y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` pasa del check no-print y falla después en `pip-audit` por vulnerabilidades no allowlisted (`GHSA-6vgw-5pg2-w6jp` en `pip 25.3` y `GHSA-5239-wwwm-4pmq` en `pygments 2.19.2`), así que el cierre queda bloqueado por el siguiente guardarraíl del gate completo.

### RCDX-009 — Resolver hallazgos activos de `pip-audit` en el gate completo
- **estado**: BLOCKED
- **objetivo**: Recuperar el paso `pip-audit` del gate completo para que deje de bloquear cierres validados por vulnerabilidades conocidas en el toolchain activo.
- **alcance permitido**:
  - determinar si los hallazgos `GHSA-6vgw-5pg2-w6jp` (`pip 25.3`) y `GHSA-5239-wwwm-4pmq` (`pygments 2.19.2`) se resuelven con upgrade reproducible o requieren allowlist temporal justificada,
  - aplicar el ajuste mínimo en pinning, setup o `docs/pip_audit_allowlist.json` con evidencia verificable,
  - mantener el gate estricto: no ocultar vulnerabilidades reales del repo sin justificación explícita.
- **fuera de alcance**:
  - cambios funcionales de producto,
  - relajar `pip-audit` globalmente o desactivarlo,
  - refactors amplios del tooling.
- **archivos o zonas probables**:
  - `requirements-dev.txt`
  - `requirements-dev.in`
  - `docs/pip_audit_allowlist.json`
  - `scripts/quality_gate_components/pip_audit_check.py`
  - `scripts/setup.py`
- **checks obligatorios**:
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `pip-audit` deja de reportar como no allowlisted `GHSA-6vgw-5pg2-w6jp` y `GHSA-5239-wwwm-4pmq`,
  - cualquier allowlist nueva queda justificada y acotada,
  - `python -m scripts.gate_pr` vuelve a avanzar más allá del paso `pip-audit`.
- **dependencias o bloqueo**: Evidencia 2026-03-27 00:03:38Z: tras corregir `check_no_print_calls(...)`, `python -m scripts.gate_pr` ya no falla por `print` en `.venv`, pero `docs/pip_audit_report.txt` registra `GHSA-6vgw-5pg2-w6jp` en `pip 25.3` y `GHSA-5239-wwwm-4pmq` en `pygments 2.19.2`; `docs/pip_audit_allowlist.json` está vacío, por lo que el gate completo queda bloqueado en `pip-audit`. Revalidacion 2026-03-27 01:09:18Z: el ajuste minimo deja `pip==26.0.1` pinneado en `requirements-dev.in` y `requirements-dev.txt`, `scripts/quality_gate_components/pip_audit_check.py` pasa a auditar el entorno canónico local y la allowlist temporal justifica `GHSA-5239-wwwm-4pmq` porque `pygments 2.19.2` sigue siendo la ultima version publicada sin fix reportado; `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_security.py tests/test_gate_pr.py` queda en verde, `python -m scripts.gate_rapido` devuelve `rc=0` y `python -m scripts.gate_pr` ya supera `pip-audit`, pero el cierre sigue bloqueado por un guardarrail posterior que escanea `.venv` (`scripts/quality_gate_components.pii_guardrail` reporta `nif` dentro de `.\.venv\Lib\site-packages\setuptools\...`).

### RCDX-010 — Excluir `.venv` del guardarrail PII/logging del gate completo
- **estado**: BLOCKED
- **objetivo**: Evitar que el guardarrail PII/logging trate como codigo del repo las claves sensibles presentes en dependencias instaladas dentro de `.venv`.
- **alcance permitido**:
  - corregir `scripts/quality_gate_components/pii_guardrail.py` para que respete los directorios excluidos del repositorio o reutilice un iterador ya filtrado,
  - añadir una regresion minima en tests para congelar que `.venv` y otros directorios excluidos no se escanean en ese guardarrail,
  - mantener intacta la deteccion de mensajes o metadata sensible en codigo propio del repositorio.
- **fuera de alcance**:
  - relajar la politica PII/logging sobre archivos del repo,
  - cambios funcionales de producto,
  - refactors amplios del quality gate.
- **archivos o zonas probables**:
  - `scripts/quality_gate_components/pii_guardrail.py`
  - `tests/test_quality_gate_security.py`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_security.py tests/test_gate_pr.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `check_pii_logging_guardrail(...)` deja de inspeccionar `.venv` y demas directorios excluidos,
  - el guardarrail sigue detectando literales o metadata sensible en codigo propio no allowlisted,
  - `python -m scripts.gate_pr` deja de fallar por claves PII presentes en `site-packages`.
- **dependencias o bloqueo**: Evidencia 2026-03-27 01:09:18Z: tras desbloquear `pip-audit`, `python -m scripts.gate_pr` avanza hasta `scripts.quality_gate_components.pii_guardrail` y falla porque `_iter_python_files(...)` recorre `root.rglob("*.py")` y solo excluye por `PII_GUARDRAIL_EXCLUDED_ROOTS` cuando la primera parte relativa coincide; como `.venv` no figura entre esas exclusiones, el guardarrail reporta `nif` en `.\.venv\Lib\site-packages\setuptools\_distutils\command\sdist.py` y rutas similares. Revalidacion 2026-03-27 02:03:43Z: `scripts/quality_gate_components/pii_guardrail.py` ya combina `SCAN_EXCLUDE_DIRS` con `PII_GUARDRAIL_EXCLUDED_ROOTS`, `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_security.py tests/test_gate_pr.py` queda en verde y `python -m scripts.gate_rapido` devuelve `rc=0`; ademas `python -m scripts.gate_pr` supera el guardarrail PII/logging, pero el cierre sigue bloqueado por un bug posterior de Ruff en Windows (`FileNotFoundError: [WinError 206] El nombre del archivo o la extension es demasiado largo` al ejecutar `check_command = [sys.executable, "-m", "ruff", "check", *python_targets]`).

### RCDX-011 — Acotar la invocacion de Ruff del gate completo en Windows
- **estado**: BLOCKED
- **objetivo**: Evitar que `python -m scripts.gate_pr` falle en Windows por una linea de comando de Ruff demasiado larga al expandir todos los targets Python versionados.
- **alcance permitido**:
  - ajustar `scripts/quality_gate_components/ruff_checks.py` para invocar Ruff con un conjunto de targets estable que no exceda el limite de Windows,
  - reutilizar o adaptar `scripts/_ruff_targets.py` si hace falta para agrupar, acotar o degradar la invocacion sin perder cobertura efectiva del repo,
  - añadir una regresion minima en tests para congelar que la invocacion principal de Ruff siga siendo ejecutable cuando el repositorio tenga muchos archivos Python versionados.
- **fuera de alcance**:
  - reducir el alcance de Ruff a un subconjunto arbitrario del repo,
  - cambios funcionales de producto,
  - refactors amplios del quality gate.
- **archivos o zonas probables**:
  - `scripts/quality_gate_components/ruff_checks.py`
  - `scripts/_ruff_targets.py`
  - `tests/test_quality_gate_ruff.py`
  - `tests/test_gate_pr.py`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_gate_pr.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `run_required_ruff_checks(...)` deja de disparar `WinError 206` en Windows,
  - Ruff sigue validando de forma determinista el codigo Python versionado del repositorio,
  - `python -m scripts.gate_pr` vuelve a avanzar mas alla del paso `ruff`.
- **dependencias o bloqueo**: Evidencia 2026-03-27 02:03:43Z: despues de pasar `pip-audit`, `pii_guardrail` y `secrets_scan`, `python -m scripts.gate_pr` falla dentro de `scripts.quality_gate_components.ruff_checks` porque `run_required_ruff_checks(...)` construye `check_command = [sys.executable, "-m", "ruff", "check", *python_targets]` y `format_command = [sys.executable, "-m", "ruff", "format", "--check", *python_targets]` con todos los archivos devueltos por `scripts._ruff_targets.obtener_targets_python(...)`; en Windows esto termina en `FileNotFoundError: [WinError 206] El nombre del archivo o la extension es demasiado largo` antes de ejecutar Ruff. Revalidacion 2026-03-27 04:08:47Z: `scripts._ruff_targets.agrupar_targets_para_comando(...)` ahora divide los `995` targets Python versionados bajo `LIMITE_COMANDO_RUFF_CHARS=30000`, `.\.venv\Scripts\python.exe -m pytest -q tests/test_ruff_targets.py tests/test_quality_gate_ruff.py tests/test_gate_pr.py` queda en verde y `python -m scripts.gate_pr` ya no dispara `WinError 206`; sin embargo, el mismo gate aborta en `ruff format --check` porque el primer lote reporta `14 files would be reformatted`, y corregir esos `14` archivos en una sola ejecucion excede el limite operativo de `10` archivos modificados por run. Revalidacion final 2026-03-27 04:13:09Z: tras sincronizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md`, `python -m scripts.gate_pr` repite el mismo bloqueo real de formateo sobre esos `14` archivos.

### RCDX-012 — Acotar los lotes de Ruff format-check al limite operativo
- **estado**: BLOCKED
- **objetivo**: Alinear los lotes de `ruff format --check` con el limite operativo de `10` archivos por ejecucion, manteniendo la proteccion contra lineas de comando demasiado largas y la cobertura determinista sobre codigo Python versionado.
- **alcance permitido**:
  - ajustar `scripts/quality_gate_components/ruff_checks.py` y/o `scripts/_ruff_targets.py` para que los lotes de Ruff respeten a la vez el limite de caracteres de Windows y un maximo estable de archivos por lote,
  - añadir regresiones minimas en tests para congelar que un lote largo siga siendo ejecutable y que un fallo de formato no agrupe mas de `10` archivos versionados,
  - mantener el uso de targets Python explicitos del repositorio sin relajar el alcance efectivo de Ruff.
- **fuera de alcance**:
  - reformatear archivos de producto reportados por Ruff,
  - relajar reglas de Ruff o desactivar `format --check`,
  - cambios funcionales de producto o refactors amplios del quality gate.
- **archivos o zonas probables**:
  - `scripts/quality_gate_components/ruff_checks.py`
  - `scripts/_ruff_targets.py`
  - `tests/test_ruff_targets.py`
  - `tests/test_quality_gate_ruff.py`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_ruff_targets.py tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py tests/test_gate_pr.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - ningun lote de `ruff format --check` supera `10` archivos versionados ni el limite de linea de comando en Windows,
  - `python -m scripts.gate_pr` mantiene corregido el `WinError 206` y, si Ruff sigue fallando, lo hace en un lote acotado al limite operativo,
  - la cobertura determinista sobre codigo Python versionado del repositorio se mantiene intacta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 04:08:01Z: tras corregir el `WinError 206`, `python -m scripts.gate_pr` ejecuta Ruff por lotes, pero `ruff format --check` falla en el primer lote con `14 files would be reformatted`; el diff incluye rutas como `clinicdesk/app/application/ml/interpretacion_ml_humana.py`, `clinicdesk/app/i18n_catalogos/pred.py` y `clinicdesk/app/pages/shared/contexto_tabla.py`. Mientras el lote fallido supere `10` archivos, una limpieza directa de formato no cabe en el limite operativo por ejecucion. Revalidacion 2026-03-27 04:04:35Z: `scripts._ruff_targets.agrupar_targets_para_comando(...)` ya permite fijar `max_targets_por_lote`, `scripts.quality_gate_components.ruff_checks` limita `ruff format --check` a `10` archivos por lote, `.\.venv\Scripts\python.exe -m pytest -q tests/test_ruff_targets.py tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py tests/test_gate_pr.py` queda en verde y `python -m scripts.gate_rapido` devuelve `rc=0`; sin embargo, `python -m scripts.gate_pr` sigue en rojo porque el lote acotado ahora expone una deuda real de formato en un unico archivo (`clinicdesk/app/application/ml/interpretacion_ml_humana.py`).

### RCDX-013 â€” Corregir el formateo Ruff pendiente en interpretacion_ml_humana.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/application/ml/interpretacion_ml_humana.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/application/ml/interpretacion_ml_humana.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere semantica ni contratos funcionales,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear otros archivos reportados historicamente por Ruff,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/application/ml/interpretacion_ml_humana.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/ml/interpretacion_ml_humana.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/application/ml/interpretacion_ml_humana.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 04:04:35Z: tras acotar `ruff format --check` a lotes de `10` archivos, `python -m scripts.gate_pr` ya no falla por un lote operativo demasiado grande y el artefacto `docs/ruff_format_diff.txt` pasa a mostrar un unico archivo con deuda real de formato: `clinicdesk/app/application/ml/interpretacion_ml_humana.py`. Revalidacion 2026-03-27 05:04:14Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/ml/interpretacion_ml_humana.py` queda en verde, `python -m scripts.gate_rapido` devuelve `rc=0` y `python -m scripts.gate_pr` avanza mas alla del archivo objetivo, pero ahora aborta por una deuda real de formato en `clinicdesk/app/application/seguros/__init__.py`; el diff de Ruff elimina solo una linea en blanco sobrante de la lista exportada, por lo que se materializa `RCDX-014` como siguiente `TODO` atomica. Revalidacion final 2026-03-27 05:06:12Z: tras actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md`, `python -m scripts.gate_rapido` se mantiene en `rc=0`.

### RCDX-014 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/seguros/__init__.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/application/seguros/__init__.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/application/seguros/__init__.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere semantica ni contratos funcionales,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear otros archivos reportados por Ruff,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/application/seguros/__init__.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/seguros/__init__.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/application/seguros/__init__.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 05:04:14Z: tras corregir `clinicdesk/app/application/ml/interpretacion_ml_humana.py`, `python -m scripts.gate_pr` pasa a fallar en `clinicdesk/app/application/seguros/__init__.py`; el diagnostico de Ruff muestra un unico ajuste de formato pendiente, consistente en eliminar una linea en blanco sobrante dentro de la lista exportada. Revalidacion 2026-03-27 06:02:40Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/seguros/__init__.py` queda en verde, `python -m scripts.gate_rapido` devuelve `rc=0` y `python -m scripts.gate_pr` avanza mas alla del archivo objetivo, pero ahora aborta por una deuda real de formato en `clinicdesk/app/application/seguros/economia_poliza.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/seguros/economia_poliza.py` confirma `1 file would be reformatted` y el diff de Ruff acota el cambio a partir una condicion `if` larga en dos lineas, por lo que se materializa `RCDX-015` como siguiente `TODO` atomica.

### RCDX-015 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/seguros/economia_poliza.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/application/seguros/economia_poliza.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/application/seguros/economia_poliza.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere semantica ni contratos funcionales,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear otros archivos reportados por Ruff,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/application/seguros/economia_poliza.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/seguros/economia_poliza.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/application/seguros/economia_poliza.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 06:02:40Z: tras corregir `clinicdesk/app/application/seguros/__init__.py`, `python -m scripts.gate_pr` pasa a fallar en `clinicdesk/app/application/seguros/economia_poliza.py`; el diagnostico de Ruff muestra un unico ajuste de formato pendiente, consistente en partir en dos lineas una condicion `if` larga dentro del calculo de cuotas vencidas. Revalidacion 2026-03-27 07:03:21Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/seguros/economia_poliza.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/application/seguros/test_economia_poliza_service.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/application/services/demo_ml_facade.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/demo_ml_facade.py` confirma `1 file would be reformatted` y el diff de Ruff acota el cambio a eliminar una linea en blanco sobrante antes de `list_dataset_versions`, por lo que se materializa `RCDX-016` como siguiente `TODO` atomica.

### RCDX-016 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/demo_ml_facade.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/application/services/demo_ml_facade.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/application/services/demo_ml_facade.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere semantica ni contratos funcionales,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear otros archivos reportados por Ruff,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/application/services/demo_ml_facade.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/demo_ml_facade.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_demo_ml_facade.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/application/services/demo_ml_facade.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 07:03:21Z: tras corregir `clinicdesk/app/application/seguros/economia_poliza.py`, `python -m scripts.gate_pr` pasa a fallar en `clinicdesk/app/application/services/demo_ml_facade.py`; el diagnostico de Ruff muestra un unico ajuste de formato pendiente, consistente en eliminar una linea en blanco sobrante antes de `list_dataset_versions`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/demo_ml_facade.py` confirma `1 file would be reformatted` y `tests/test_demo_ml_facade.py` queda identificado como suite especifica del area afectada. Revalidacion 2026-03-27 08:03:17Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/demo_ml_facade.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_demo_ml_facade.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/application/services/ml_centro_guiado_service.py` y `clinicdesk/app/application/services/ml_playbooks_service.py`; `.\.venv\Scripts\python.exe -m ruff format --check` confirma `1 file would be reformatted` en ambos, por lo que se materializa `RCDX-017` como siguiente `TODO` atomica para el primer archivo del lote. Revalidacion final 2026-03-27 08:05:04Z: tras sincronizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md`, `python -m scripts.gate_rapido` se mantiene en `rc=0` y `python -m scripts.gate_pr` repite el mismo bloqueo de formato en esos dos archivos.

### RCDX-017 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/ml_centro_guiado_service.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/application/services/ml_centro_guiado_service.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/application/services/ml_centro_guiado_service.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere semantica ni contratos funcionales,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear otros archivos reportados por Ruff,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/application/services/ml_centro_guiado_service.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_centro_guiado_service.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_ml_centro_guiado_service.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/application/services/ml_centro_guiado_service.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 08:03:17Z: tras corregir `clinicdesk/app/application/services/demo_ml_facade.py`, `python -m scripts.gate_pr` pasa a fallar en un lote de `ruff format --check` que incluye `clinicdesk/app/application/services/ml_centro_guiado_service.py` y `clinicdesk/app/application/services/ml_playbooks_service.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_centro_guiado_service.py` confirma `1 file would be reformatted`, `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_playbooks_service.py` confirma la deuda residual del siguiente archivo y `tests/test_ml_centro_guiado_service.py` queda identificado como suite especifica del area afectada. Revalidacion 2026-03-27 09:02:33Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_centro_guiado_service.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_ml_centro_guiado_service.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/application/services/ml_playbooks_service.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_playbooks_service.py` confirma `1 file would be reformatted` y el diff de Ruff acota el cambio a partir la firma larga de `_pasos_playbook(...)`, por lo que se materializa `RCDX-018` como siguiente `TODO` atomica.

### RCDX-018 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/ml_playbooks_service.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/application/services/ml_playbooks_service.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/application/services/ml_playbooks_service.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere semantica ni contratos funcionales,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear otros archivos reportados por Ruff,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/application/services/ml_playbooks_service.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_playbooks_service.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_ml_playbooks_service.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/application/services/ml_playbooks_service.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 09:02:33Z: tras corregir `clinicdesk/app/application/services/ml_centro_guiado_service.py`, `python -m scripts.gate_pr` pasa a fallar en `clinicdesk/app/application/services/ml_playbooks_service.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_playbooks_service.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a partir la firma larga de `_pasos_playbook(...)` y `tests/test_ml_playbooks_service.py` queda identificado como suite especifica del area afectada. Revalidacion 2026-03-27 10:18:54Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/ml_playbooks_service.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_ml_playbooks_service.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/application/services/seguimiento_operativo_ml_service.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` confirma `1 file would be reformatted` y el diff de Ruff acota el cambio a eliminar una linea en blanco final sobrante, por lo que se materializa `RCDX-019` como siguiente `TODO` atomica. Revalidacion final 2026-03-27 10:24:04Z: tras sincronizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md`, `python -m scripts.gate_rapido` se mantiene en `rc=0`.

### RCDX-019 - Corregir el formateo Ruff pendiente en clinicdesk/app/application/services/seguimiento_operativo_ml_service.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/application/services/seguimiento_operativo_ml_service.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere semantica ni contratos funcionales,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear otros archivos reportados por Ruff,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/application/services/seguimiento_operativo_ml_service.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/seguimiento_operativo_ml_service.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_seguimiento_operativo_ml_service.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 10:18:54Z: tras corregir `clinicdesk/app/application/services/ml_playbooks_service.py`, `python -m scripts.gate_pr` pasa a fallar en `clinicdesk/app/application/services/seguimiento_operativo_ml_service.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a eliminar una linea en blanco final sobrante y `tests/test_seguimiento_operativo_ml_service.py` queda identificado como suite especifica del area afectada. Revalidacion 2026-03-27 10:34:30Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/application/services/seguimiento_operativo_ml_service.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_seguimiento_operativo_ml_service.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en un lote que incluye `clinicdesk/app/i18n_catalogos/pred.py` y `clinicdesk/app/i18n_catalogos/ux.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/pred.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a eliminar lineas en blanco sobrantes y agregar comas finales faltantes dentro del catalogo, `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py` confirma la deuda residual del segundo archivo del lote y `tests/test_i18n_catalog.py` queda identificado como suite especifica del area afectada. Para mantener la disciplina de una sola incidencia por ejecucion, se materializa `RCDX-020` como siguiente `TODO` atomica.

### RCDX-020 - Corregir el formateo Ruff pendiente en clinicdesk/app/i18n_catalogos/pred.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/i18n_catalogos/pred.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/i18n_catalogos/pred.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere las claves ni el contrato semantico del catalogo,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear `clinicdesk/app/i18n_catalogos/ux.py` en esta misma ejecucion,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/i18n_catalogos/pred.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/pred.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_i18n_catalog.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/i18n_catalogos/pred.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 10:34:30Z: tras corregir `clinicdesk/app/application/services/seguimiento_operativo_ml_service.py`, `python -m scripts.gate_pr` pasa a fallar en un lote de `ruff format --check` que incluye `clinicdesk/app/i18n_catalogos/pred.py` y `clinicdesk/app/i18n_catalogos/ux.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/pred.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a eliminar lineas en blanco sobrantes y agregar comas finales faltantes dentro del catalogo, `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py` confirma la deuda residual del siguiente archivo y `tests/test_i18n_catalog.py` queda identificado como suite especifica del area afectada. Revalidacion 2026-03-27 10:53:09Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/pred.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_i18n_catalog.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/i18n_catalogos/ux.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py` confirma `1 file would be reformatted` y el diff de Ruff acota el cambio a eliminar dos lineas en blanco sobrantes entre grupos de claves, por lo que se materializa `RCDX-021` como siguiente `TODO` atomica.

### RCDX-021 - Corregir el formateo Ruff pendiente en clinicdesk/app/i18n_catalogos/ux.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/i18n_catalogos/ux.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/i18n_catalogos/ux.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere las claves ni el contrato semantico del catalogo,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear otros catalogos i18n o archivos adicionales en esta misma ejecucion,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/i18n_catalogos/ux.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_i18n_catalog.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/i18n_catalogos/ux.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 10:53:09Z: tras corregir `clinicdesk/app/i18n_catalogos/pred.py`, `python -m scripts.gate_pr` pasa a fallar en `clinicdesk/app/i18n_catalogos/ux.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a eliminar dos lineas en blanco sobrantes entre grupos de claves del catalogo y `tests/test_i18n_catalog.py` queda identificado como suite especifica del area afectada. Revalidacion 2026-03-27 11:14:33Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/i18n_catalogos/ux.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_i18n_catalog.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en un lote que incluye `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` y `clinicdesk/app/pages/citas/logging_payloads.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a partir en varias lineas dos llamadas largas a `form.addRow(...)`, `tests/ui/test_cita_form_dialog.py` queda identificado como suite especifica del area afectada y `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/logging_payloads.py` confirma la deuda residual del segundo archivo del lote, por lo que se materializa `RCDX-022` como siguiente `TODO` atomica.

### RCDX-022 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el contrato UI ni la validacion del formulario,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear `clinicdesk/app/pages/citas/logging_payloads.py` en esta misma ejecucion,
  - cambios funcionales de producto,
  - cambios en el loteo o reglas del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_cita_form_dialog.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` deja de aparecer en `ruff format --check`,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta,
  - el diff del archivo queda limitado a formato sin cambios funcionales.
- **dependencias o bloqueo**: Evidencia 2026-03-27 11:14:33Z: tras corregir `clinicdesk/app/i18n_catalogos/ux.py`, `python -m scripts.gate_pr` pasa a fallar en un lote de `ruff format --check` que incluye `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` y `clinicdesk/app/pages/citas/logging_payloads.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a partir en varias lineas dos llamadas largas a `form.addRow(...)`, `tests/ui/test_cita_form_dialog.py` queda identificado como suite especifica del area afectada y `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/logging_payloads.py` confirma la deuda residual del siguiente archivo del lote. Revalidacion 2026-03-27 11:33:25Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_cita_form_dialog.py` falla en `test_cita_form_foco_en_primer_error` porque `dialogo.ed_inicio.hasFocus()` queda en `False` tras `dialogo._on_ok()`, `python -m scripts.gate_rapido` devuelve `rc=0` y `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `clinicdesk/app/pages/citas/logging_payloads.py`. Como el test roto del area tiene prioridad sobre la siguiente deuda de Ruff, se materializa `RCDX-023` como siguiente `TODO` atomica.

### RCDX-023 - Restablecer el foco del primer error en clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py
- **estado**: BLOCKED
- **objetivo**: Corregir la regresion por la que `CitaFormDialog._on_ok()` no devuelve el foco al primer campo con error, restableciendo el contrato cubierto por `tests/ui/test_cita_form_dialog.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py` y, si hace falta para reflejar el contrato real, `tests/ui/test_cita_form_dialog.py`,
  - mantener intacto el resto del flujo del formulario y su validacion,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear `clinicdesk/app/pages/citas/logging_payloads.py` en esta misma ejecucion,
  - cambios funcionales no relacionados con el manejo de foco del formulario,
  - cambios en el quality gate o en otros dialogs UI.
- **archivos o zonas probables**:
  - `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py`
  - `tests/ui/test_cita_form_dialog.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_cita_form_dialog.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `test_cita_form_foco_en_primer_error` queda en verde,
  - el foco vuelve al primer campo con error tras un submit invalido sin romper el resto de pruebas del dialogo,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 11:33:25Z: tras completar el formateo de `clinicdesk/app/pages/citas/dialogs/dialog_cita_form.py`, `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_cita_form_dialog.py` falla en `test_cita_form_foco_en_primer_error` porque `dialogo.ed_inicio.hasFocus()` queda en `False` despues de `dialogo._on_ok()`. `python -m scripts.gate_pr` ya no queda bloqueado por `dialog_cita_form.py`, pero si revela una deuda residual de formato en `clinicdesk/app/pages/citas/logging_payloads.py`; esa incidencia queda pospuesta porque el test roto del area tiene prioridad superior. Revalidacion 2026-03-27 12:57:29Z: `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_cita_form_dialog.py` queda en verde tras ajustar el test para mostrar el dialogo y validar el foco con la ventana visible, `python -m scripts.gate_rapido` devuelve `rc=0` y `python -m scripts.gate_pr` avanza mas alla del bloqueo del area, pero ahora aborta por una deuda real de formato en `clinicdesk/app/pages/citas/logging_payloads.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/logging_payloads.py` confirma `1 file would be reformatted` y `.\.venv\Scripts\python.exe -m pytest -q tests/test_citas_calendario_logging.py` pasa, por lo que se materializa `RCDX-024` como siguiente `TODO` atomica.

### RCDX-024 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/citas/logging_payloads.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/pages/citas/logging_payloads.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/pages/citas/logging_payloads.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el payload de logging del calendario,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambiar el contrato del payload de logging o sus `reason_code`,
  - tocar otros archivos de citas en esta misma ejecucion,
  - cambios funcionales de producto o del quality gate.
- **archivos o zonas probables**:
  - `clinicdesk/app/pages/citas/logging_payloads.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/logging_payloads.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_citas_calendario_logging.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/pages/citas/logging_payloads.py` deja de aparecer en `ruff format --check`,
  - `tests/test_citas_calendario_logging.py` queda en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 12:57:16Z: tras validar `RCDX-023`, `python -m scripts.gate_pr` pasa a fallar en `clinicdesk/app/pages/citas/logging_payloads.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/logging_payloads.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a partir en varias lineas la firma de `payload_log_error_calendario(...)` y `.\.venv\Scripts\python.exe -m pytest -q tests/test_citas_calendario_logging.py` queda identificado en verde como suite especifica del area afectada. Revalidacion 2026-03-27 12:13:11Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/citas/logging_payloads.py` queda en verde, `.\.venv\Scripts\python.exe -m pytest -q tests/test_citas_calendario_logging.py` pasa y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` confirma `1 file would be reformatted`, `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py` falla en `test_paciente_form_validacion_inline_y_cta` y `test_paciente_form_foco_en_primer_error`, y una sonda local con el dialogo mostrado devuelve `email_visible True` y `documento_focus True`; por prioridad contractual, la suite rota del area pasa delante de la deuda de Ruff y se materializa `RCDX-025` como siguiente `TODO` atomica.

### RCDX-025 - Alinear tests/ui/test_paciente_form_dialog.py con el contrato visible de PacienteFormDialog
- **estado**: BLOCKED
- **objetivo**: Corregir la regresion de la suite UI que valida visibilidad y foco sobre `PacienteFormDialog` sin mostrar el dialogo, alineando `tests/ui/test_paciente_form_dialog.py` con el contrato real del formulario visible.
- **alcance permitido**:
  - ajustar unicamente `tests/ui/test_paciente_form_dialog.py` y, si hace falta para el wiring del test, `tests/ui/conftest.py`,
  - mostrar el dialogo y validar `isVisible()` y `hasFocus()` con la ventana visible, manteniendo intacta la logica de producto,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` en esta misma ejecucion,
  - cambios funcionales de producto en `PacienteFormDialog` sin evidencia adicional que contradiga la sonda local,
  - cambios en el quality gate o en otros dialogs UI.
- **archivos o zonas probables**:
  - `tests/ui/test_paciente_form_dialog.py`
  - `tests/ui/conftest.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `test_paciente_form_validacion_inline_y_cta` y `test_paciente_form_foco_en_primer_error` quedan en verde,
  - la suite valida los estados de error y foco con el dialogo visible sin introducir cambios funcionales en el formulario,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 12:13:11Z: tras completar `RCDX-024`, `python -m scripts.gate_pr` pasa a fallar en `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` confirma `1 file would be reformatted`, pero la prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py` falla en `test_paciente_form_validacion_inline_y_cta` (`dialogo._labels_error["email"].isVisible()` queda en `False`) y `test_paciente_form_foco_en_primer_error` (`dialogo.txt_documento.hasFocus()` queda en `False`). La sonda local ejecutada con el dialogo mostrado devuelve `email_visible True` y `documento_focus True`, lo que acota la siguiente incidencia a la suite UI y deja la deuda de Ruff en `paciente_form.py` para una ejecucion posterior. Revalidacion 2026-03-27 12:37:06Z: `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py` queda en verde tras mostrar el dialogo, validar `isVisible()`/`hasFocus()` con la ventana visible y cerrarlo explicitamente para evitar el modal de descarte en teardown; `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del bloqueo del area y ahora aborta por deuda real de formato en `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` confirma `1 file would be reformatted`, por lo que se materializa `RCDX-026` como siguiente `TODO` atomica.

### RCDX-026 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/pacientes/dialogs/paciente_form.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el contrato visible del formulario ni la validacion ya reestablecida en la suite UI,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambios funcionales de producto en `PacienteFormDialog`,
  - reformatear otros archivos en esta misma ejecucion,
  - cambios en el quality gate o en otros dialogs UI.
- **archivos o zonas probables**:
  - `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` deja de aparecer en `ruff format --check`,
  - `tests/ui/test_paciente_form_dialog.py` sigue en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 12:37:06Z: tras validar `RCDX-025`, `python -m scripts.gate_pr` pasa a fallar por deuda real de formato en `clinicdesk/app/pages/pacientes/dialogs/paciente_form.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` confirma `1 file would be reformatted` y el diff del gate completo acota el cambio a varias llamadas largas de `form.addRow(...)`, `QDate(...)` y `setText(...)`. `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py` queda identificado en verde como suite especifica del area afectada. Revalidacion 2026-03-27 13:53:25Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/pacientes/dialogs/paciente_form.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_paciente_form_dialog.py` pasa (`4 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/pages/prediccion_ausencias/page.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/prediccion_ausencias/page.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a una llamada larga a `setText(...)` y a la construccion de `contexto` en `_registrar_telemetria_monitor_ml`, y `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_estabilidad.py` pasa, por lo que se materializa `RCDX-027` como siguiente `TODO` atomica.

### RCDX-027 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/prediccion_ausencias/page.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/pages/prediccion_ausencias/page.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/pages/prediccion_ausencias/page.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el contrato UI ni la telemetria deduplicada de la pagina,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambios funcionales de producto en `PagePrediccionAusencias`,
  - reformatear otros archivos en esta misma ejecucion,
  - cambios en el quality gate o en otros modulos de prediccion.
- **archivos o zonas probables**:
  - `clinicdesk/app/pages/prediccion_ausencias/page.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/prediccion_ausencias/page.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_estabilidad.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/pages/prediccion_ausencias/page.py` deja de aparecer en `ruff format --check`,
  - `tests/test_prediccion_ausencias_page_estabilidad.py` sigue en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 13:53:25Z: tras validar `RCDX-026`, `python -m scripts.gate_pr` pasa a fallar por deuda real de formato en `clinicdesk/app/pages/prediccion_ausencias/page.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/prediccion_ausencias/page.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a una llamada larga a `setText(...)` y a la construccion de `contexto` en `_registrar_telemetria_monitor_ml`, y `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_estabilidad.py` queda identificado en verde como suite especifica del area afectada. Revalidacion 2026-03-27 13:14:04Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/prediccion_ausencias/page.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_estabilidad.py` pasa (`9 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por una deuda real de formato en `clinicdesk/app/pages/shared/contexto_tabla.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/shared/contexto_tabla.py` confirma `1 file would be reformatted`, pero la prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py` falla en `test_contexto_tabla_restaurar_seleccion_y_scroll` al exigir un scroll vertical imposible para la tabla visible; la sonda local devuelve `scroll_max 1`, `scroll_actual 1` y `scroll_capturado 1`, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py` pasa, por lo que se materializa `RCDX-028` como siguiente `TODO` atomica antes de retomar la deuda de Ruff en `clinicdesk/app/pages/shared/contexto_tabla.py`.

### RCDX-028 - Alinear tests/ui/test_contexto_tabla.py con el contrato visible de restaurar_contexto_tabla
- **estado**: BLOCKED
- **objetivo**: Corregir la regresion de la suite UI que exige un scroll vertical no alcanzable para la tabla visible, alineando `tests/ui/test_contexto_tabla.py` con el contrato real de `capturar_contexto_tabla()` y `restaurar_contexto_tabla()`.
- **alcance permitido**:
  - ajustar unicamente `tests/ui/test_contexto_tabla.py` y, si hace falta para el wiring del test, `tests/ui/conftest.py`,
  - validar el scroll restaurado contra el valor realmente capturado por la tabla visible o contra un setup que garantice ese rango,
  - mantener intacta la logica de `clinicdesk/app/pages/shared/contexto_tabla.py`,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear `clinicdesk/app/pages/shared/contexto_tabla.py` en esta misma ejecucion,
  - cambios funcionales en el helper de contexto de tabla sin evidencia adicional,
  - cambios en el quality gate o en otras suites UI.
- **archivos o zonas probables**:
  - `tests/ui/test_contexto_tabla.py`
  - `tests/ui/conftest.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `test_contexto_tabla_restaurar_seleccion_y_scroll` queda en verde,
  - la suite valida el scroll restaurado contra el contrato visible y no contra un valor clamped fuera de rango,
  - `clinicdesk/app/pages/shared/contexto_tabla.py` permanece sin cambios funcionales,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 13:14:04Z: tras completar `RCDX-027`, `python -m scripts.gate_pr` pasa a fallar en `clinicdesk/app/pages/shared/contexto_tabla.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/shared/contexto_tabla.py` confirma `1 file would be reformatted`, pero la prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py` falla en `test_contexto_tabla_restaurar_seleccion_y_scroll`; la asercion `tabla.verticalScrollBar().value() == 7` queda en rojo con valor real `1`. Una sonda local con la tabla visible devuelve `scroll_max 1`, `scroll_actual 1` y `scroll_capturado 1`, y `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py` pasa, lo que acota la siguiente incidencia a la suite UI y deja la deuda de Ruff en `clinicdesk/app/pages/shared/contexto_tabla.py` para una ejecucion posterior. Revalidacion 2026-03-27 13:33:18Z: `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py` pasa (`2 passed`) tras comparar el scroll restaurado con `contexto.scroll_vertical` y con el valor realmente capturado por la tabla visible; `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py` pasa (`3 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del bloqueo del area y ahora aborta por deuda real de formato en `clinicdesk/app/pages/shared/contexto_tabla.py`; `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/shared/contexto_tabla.py` confirma `1 file would be reformatted` y el diff de Ruff acota el cambio a partir en varias lineas el import largo inicial, por lo que se materializa `RCDX-029` como siguiente `TODO` atomica.

### RCDX-029 - Corregir el formateo Ruff pendiente en clinicdesk/app/pages/shared/contexto_tabla.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `clinicdesk/app/pages/shared/contexto_tabla.py`.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/pages/shared/contexto_tabla.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el contrato de `capturar_contexto_tabla()` y `restaurar_contexto_tabla()` ya revalidado por las suites del area,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambios funcionales en `clinicdesk/app/pages/shared/contexto_tabla.py`,
  - retoques adicionales en `tests/ui/test_contexto_tabla.py` o `tests/ui/test_contexto_tabla_puro.py` ya validados en verde,
  - cambios en el quality gate o en otras suites UI.
- **archivos o zonas probables**:
  - `clinicdesk/app/pages/shared/contexto_tabla.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/shared/contexto_tabla.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `clinicdesk/app/pages/shared/contexto_tabla.py` deja de aparecer en `ruff format --check`,
  - `tests/ui/test_contexto_tabla.py` y `tests/ui/test_contexto_tabla_puro.py` siguen en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 13:33:18Z: tras validar `RCDX-028`, `python -m scripts.gate_pr` ya no falla por la suite UI del area y ahora aborta por deuda real de formato en `clinicdesk/app/pages/shared/contexto_tabla.py`. `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/shared/contexto_tabla.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a partir en varias lineas el import largo desde `clinicdesk.app.ui.ux.contexto_tabla`, y `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py` (`2 passed`) junto con `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py` (`3 passed`) dejan el contrato funcional del area identificado en verde. Revalidacion 2026-03-27 13:53:22Z: `.\.venv\Scripts\python.exe -m ruff format --check clinicdesk/app/pages/shared/contexto_tabla.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla.py` pasa (`2 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_contexto_tabla_puro.py` pasa (`3 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/gate_pr.py`; `.\.venv\Scripts\python.exe -m ruff format --check scripts/gate_pr.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a una unica linea dentro de `validar_contrato_reason_codes_doc`, y la inspeccion de `tests/test_gate_pr.py`, `tests/test_gate_reason_codes_docs_sync.py` y `tests/test_quality_gate_reason_codes_doc_check.py` deja identificada la cobertura especifica del area, por lo que se materializa `RCDX-030` como siguiente `TODO` atomica.

### RCDX-030 - Corregir el formateo Ruff pendiente en scripts/gate_pr.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `scripts/gate_pr.py`.
- **alcance permitido**:
  - ajustar unicamente `scripts/gate_pr.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el contrato del entrypoint canonico ni el check documental de `reason_code`,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambios funcionales en `scripts/gate_pr.py`,
  - retoques adicionales en `clinicdesk/app/pages/shared/contexto_tabla.py` o en las suites de contexto de tabla ya revalidadas en verde,
  - cambios en otros scripts del quality gate o en la documentacion de `reason_code`.
- **archivos o zonas probables**:
  - `scripts/gate_pr.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check scripts/gate_pr.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_pr.py tests/test_gate_reason_codes_docs_sync.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `scripts/gate_pr.py` deja de aparecer en `ruff format --check`,
  - `tests/test_gate_pr.py` y `tests/test_gate_reason_codes_docs_sync.py` siguen en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 13:53:22Z: tras validar `RCDX-029`, `python -m scripts.gate_pr` ya no falla por `clinicdesk/app/pages/shared/contexto_tabla.py` y ahora aborta por deuda real de formato en `scripts/gate_pr.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/gate_pr.py` confirma `1 file would be reformatted`; el diff de Ruff acota el cambio a colapsar en una sola linea el `raise ErrorContratoReasonCodesDoc(...)` dentro de `validar_contrato_reason_codes_doc`, y la inspeccion estatica de `tests/test_gate_pr.py`, `tests/test_gate_reason_codes_docs_sync.py` y `tests/test_quality_gate_reason_codes_doc_check.py` deja identificada la cobertura especifica del area. Revalidacion 2026-03-27 14:14:05Z: `.\.venv\Scripts\python.exe -m ruff format --check scripts/gate_pr.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_pr.py tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py` pasa (`14 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/quality_gate_components/bloqueo_operativo.py`; `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/bloqueo_operativo.py` confirma `1 file would be reformatted`, el diff de Ruff acota el cambio a una unica linea en `reportar_bloqueo_operativo_doctor` y la inspeccion de `tests/test_gate_pr.py`, `tests/test_gate_rapido.py` y `tests/test_gate_operational_contract_smoke.py` deja identificada la cobertura especifica del area, por lo que se materializa `RCDX-031` como siguiente `TODO` atomica.

### RCDX-031 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/bloqueo_operativo.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `scripts/quality_gate_components/bloqueo_operativo.py`.
- **alcance permitido**:
  - ajustar unicamente `scripts/quality_gate_components/bloqueo_operativo.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el contrato compartido de bloqueo operativo entre `gate_pr` y `gate_rapido`,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambios funcionales en `scripts/quality_gate_components/bloqueo_operativo.py`,
  - retoques adicionales en `scripts/gate_pr.py` ya revalidado en verde,
  - cambios en otros scripts del quality gate o en la documentacion del contrato operativo.
- **archivos o zonas probables**:
  - `scripts/quality_gate_components/bloqueo_operativo.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/bloqueo_operativo.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_pr.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `scripts/quality_gate_components/bloqueo_operativo.py` deja de aparecer en `ruff format --check`,
  - `tests/test_gate_pr.py`, `tests/test_gate_rapido.py` y `tests/test_gate_operational_contract_smoke.py` siguen en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 14:14:05Z: tras validar `RCDX-030`, `python -m scripts.gate_pr` ya no falla por `scripts/gate_pr.py` y ahora aborta por deuda real de formato en `scripts/quality_gate_components/bloqueo_operativo.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/bloqueo_operativo.py` confirma `1 file would be reformatted`; el diff de Ruff acota el cambio a colapsar en una sola linea el `sys.stderr.write(...)` de `validaciones_no_ejecutadas` dentro de `reportar_bloqueo_operativo_doctor`, y la inspeccion estatica de `tests/test_gate_pr.py`, `tests/test_gate_rapido.py` y `tests/test_gate_operational_contract_smoke.py` deja identificada la cobertura especifica del area. Revalidacion 2026-03-27 14:35:09Z: `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/bloqueo_operativo.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_pr.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` pasa (`13 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/quality_gate_components/contrato_reason_codes_doc.py` y `scripts/quality_gate_components/ejecucion_canonica.py`; la prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` falla en dos tests que hardcodean `.venv/bin/python`, mientras la inspeccion estatica de `scripts/quality_gate_components/toolchain.py` confirma que el helper canonico resuelve `.venv/Scripts/python.exe` en Windows, por lo que corresponde materializar primero una tarea de alineacion de la suite antes de retomar la deuda de Ruff.

### RCDX-032 - Alinear tests/test_ejecucion_canonica.py con el interprete esperado por plataforma
- **estado**: BLOCKED
- **objetivo**: Corregir la regresion de `tests/test_ejecucion_canonica.py` que hardcodea una ruta POSIX del `.venv` y falla en Windows antes de retomar la siguiente deuda de formato del quality gate.
- **alcance permitido**:
  - ajustar unicamente `tests/test_ejecucion_canonica.py` y, si hace falta para no duplicar logica, reutilizar el helper canonico que resuelve el interprete esperado del repo,
  - validar las expectativas de reejecucion y bloqueo contra la ruta realmente resuelta por plataforma,
  - mantener intacta la logica de `scripts/quality_gate_components/ejecucion_canonica.py` salvo que la evidencia de la propia suite demuestre un defecto funcional real,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear `scripts/quality_gate_components/contrato_reason_codes_doc.py` o `scripts/quality_gate_components/ejecucion_canonica.py` en esta misma ejecucion,
  - cambios funcionales en el helper canonico sin evidencia nueva adicional,
  - cambios en otros tests del quality gate fuera del area de `ejecucion_canonica`.
- **archivos o zonas probables**:
  - `tests/test_ejecucion_canonica.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `tests/test_ejecucion_canonica.py` pasa en este entorno Windows,
  - las pruebas dejan de hardcodear `.venv/bin/python` y validan la ruta del interprete esperada por plataforma o por helper canonico,
  - `scripts/quality_gate_components/ejecucion_canonica.py` permanece sin cambios funcionales salvo evidencia nueva,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 14:35:09Z: tras validar `RCDX-031`, `python -m scripts.gate_pr` avanza y revela deudas de formato en `scripts/quality_gate_components/contrato_reason_codes_doc.py` y `scripts/quality_gate_components/ejecucion_canonica.py`, pero la prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` falla en `test_resolver_ejecucion_canonica_reejecuta_con_venv_repo` y `test_resolver_ejecucion_canonica_bloquea_si_python_repo_no_es_ejecutable`; en paralelo, `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py` pasa (`9 passed`) y la inspeccion estatica de `tests/test_ejecucion_canonica.py`, `scripts/quality_gate_components/ejecucion_canonica.py` y `scripts/quality_gate_components/toolchain.py` muestra que la suite crea y espera `.venv/bin/python` mientras el helper canonico resuelve `.venv/Scripts/python.exe` en Windows. Por prioridad contractual, primero debe alinearse la suite con el contrato visible del helper antes de retomar el lote de Ruff. Revalidacion 2026-03-27 14:54:48Z: `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py` pasa (`6 passed`) tras reutilizar `ejecucion_canonica.python_repo(repo_root)` y forzar el caso no ejecutable mediante `os.access`, `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` pasa (`8 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del area y ahora aborta por deuda real de formato en `scripts/quality_gate_components/contrato_reason_codes_doc.py` y `scripts/quality_gate_components/ejecucion_canonica.py`; `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/contrato_reason_codes_doc.py` y `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ejecucion_canonica.py` confirman `1 file would be reformatted` en cada archivo, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py` pasa (`9 passed`), por lo que se materializa `RCDX-033` como siguiente `TODO` atomica.

### RCDX-033 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/contrato_reason_codes_doc.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `scripts/quality_gate_components/contrato_reason_codes_doc.py`.
- **alcance permitido**:
  - ajustar unicamente `scripts/quality_gate_components/contrato_reason_codes_doc.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el parser ni el contrato documental de `reason_code`,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambios funcionales en `scripts/quality_gate_components/contrato_reason_codes_doc.py`,
  - retoques adicionales en `scripts/quality_gate_components/ejecucion_canonica.py` o en `tests/test_ejecucion_canonica.py` ya revalidados,
  - cambios en otros scripts del quality gate o en la documentacion fuera del bloque contractual afectado.
- **archivos o zonas probables**:
  - `scripts/quality_gate_components/contrato_reason_codes_doc.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/contrato_reason_codes_doc.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `scripts/quality_gate_components/contrato_reason_codes_doc.py` deja de aparecer en `ruff format --check`,
  - `tests/test_gate_reason_codes_docs_sync.py` y `tests/test_quality_gate_reason_codes_doc_check.py` siguen en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 14:54:48Z: tras validar `RCDX-032`, `python -m scripts.gate_pr` ya no falla por la suite de `ejecucion_canonica` y ahora aborta por deuda real de formato en `scripts/quality_gate_components/contrato_reason_codes_doc.py` y `scripts/quality_gate_components/ejecucion_canonica.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/contrato_reason_codes_doc.py` confirma `1 file would be reformatted`, el diff de Ruff del gate completo acota el cambio a colapsar una excepcion corta y partir dos `raise ErrorContratoReasonCodesDoc(...)` largos en el parser del bloque documental, y `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py` pasa (`9 passed`). Al no haber evidencia nueva de bug critico ni tests en rojo en ese area, corresponde atacar primero este archivo por orden del diff antes de retomar `scripts/quality_gate_components/ejecucion_canonica.py` en una ejecucion posterior. Revalidacion 2026-03-27 15:14:14Z: `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/contrato_reason_codes_doc.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_gate_reason_codes_docs_sync.py tests/test_quality_gate_reason_codes_doc_check.py` pasa (`9 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/quality_gate_components/ejecucion_canonica.py`; `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ejecucion_canonica.py` confirma `1 file would be reformatted` y `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` pasa (`14 passed`), por lo que se materializa `RCDX-034` como siguiente `TODO` atomica.

### RCDX-034 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/ejecucion_canonica.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `scripts/quality_gate_components/ejecucion_canonica.py`.
- **alcance permitido**:
  - ajustar unicamente `scripts/quality_gate_components/ejecucion_canonica.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el contrato canonico de reejecucion/bloqueo por interprete del repo,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambios funcionales en `scripts/quality_gate_components/ejecucion_canonica.py`,
  - retoques adicionales en `scripts/quality_gate_components/contrato_reason_codes_doc.py` o en `tests/test_ejecucion_canonica.py` ya revalidados,
  - cambios en otros scripts del quality gate o en la documentacion fuera del area del helper canonico.
- **archivos o zonas probables**:
  - `scripts/quality_gate_components/ejecucion_canonica.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ejecucion_canonica.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `scripts/quality_gate_components/ejecucion_canonica.py` deja de aparecer en `ruff format --check`,
  - `tests/test_ejecucion_canonica.py`, `tests/test_gate_rapido.py` y `tests/test_gate_operational_contract_smoke.py` siguen en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 15:14:14Z: tras validar `RCDX-033`, `python -m scripts.gate_pr` ya no falla por `scripts/quality_gate_components/contrato_reason_codes_doc.py` y ahora aborta por deuda real de formato en `scripts/quality_gate_components/ejecucion_canonica.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ejecucion_canonica.py` confirma `1 file would be reformatted`, el diff de Ruff del gate completo acota el cambio a eliminar lineas en blanco sobrantes y partir la firma de `reejecutar_en_python_objetivo(...)`, y `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` pasa (`14 passed`). Al no haber evidencia nueva de bug critico ni tests en rojo en ese area, corresponde atacar este archivo en la siguiente ejecucion atomica. Revalidacion 2026-03-27 15:34:14Z: `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ejecucion_canonica.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_ejecucion_canonica.py tests/test_gate_rapido.py tests/test_gate_operational_contract_smoke.py` pasa (`14 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/quality_gate_components/ruff_checks.py` y `scripts/quality_gate_components/toolchain.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ruff_checks.py` y `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` confirman `1 file would be reformatted` en cada archivo, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` falla en `test_cargar_toolchain_esperado_lee_versiones_desde_lock`, por lo que la prioridad real cambia antes de retomar el siguiente lote de Ruff y se materializa `RCDX-035`.

### RCDX-035 - Alinear tests/test_toolchain_diagnostico.py con el interprete esperado por plataforma
- **estado**: BLOCKED
- **objetivo**: Corregir la regresion de `tests/test_toolchain_diagnostico.py` que hardcodea una ruta POSIX del `.venv` y falla en Windows antes de retomar las siguientes deudas de formato del quality gate.
- **alcance permitido**:
  - ajustar unicamente `tests/test_toolchain_diagnostico.py` y, si hace falta para no duplicar logica, reutilizar el helper canonico que resuelve el interprete esperado del repo,
  - validar la expectativa de `cargar_interprete_esperado(repo_root).python_repo` contra la ruta realmente resuelta por plataforma,
  - mantener intacta la logica de `scripts/quality_gate_components/toolchain.py` salvo que la evidencia de la propia suite demuestre un defecto funcional real,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear `scripts/quality_gate_components/ruff_checks.py` o `scripts/quality_gate_components/toolchain.py` en esta misma ejecucion,
  - cambios funcionales en el helper canonico de `toolchain` sin evidencia nueva adicional,
  - cambios en otros tests del quality gate fuera del area de `toolchain`.
- **archivos o zonas probables**:
  - `tests/test_toolchain_diagnostico.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_entorno_python.py tests/test_gate_pr.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `tests/test_toolchain_diagnostico.py` pasa en este entorno Windows,
  - la suite deja de hardcodear `.venv/bin/python` y valida la ruta del interprete esperada por plataforma o por helper canonico,
  - `scripts/quality_gate_components/toolchain.py` permanece sin cambios funcionales salvo evidencia nueva,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 15:34:14Z: tras validar `RCDX-034`, `python -m scripts.gate_pr` avanza y revela deudas de formato en `scripts/quality_gate_components/ruff_checks.py` y `scripts/quality_gate_components/toolchain.py`, pero la prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` falla en `test_cargar_toolchain_esperado_lee_versiones_desde_lock`; en paralelo, `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ruff_checks.py` y `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` confirman `1 file would be reformatted` en cada archivo, y la inspeccion estatica de `tests/test_toolchain_diagnostico.py` junto con `scripts/quality_gate_components/toolchain.py` muestra que la suite todavia espera `.venv/bin/python` mientras `_python_repo()` resuelve `.venv/Scripts/python.exe` en Windows. Por prioridad contractual, primero debe alinearse la suite con el contrato visible del helper antes de retomar el lote de Ruff. Revalidacion 2026-03-27 15:53:14Z: `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py` pasa (`6 passed`) tras validar la ruta del interprete segun plataforma, `.\.venv\Scripts\python.exe -m pytest -q tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`7 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`31 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla de la suite corregida y ahora aborta por deuda real de formato en `scripts/quality_gate_components/ruff_checks.py` y `scripts/quality_gate_components/toolchain.py`; `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ruff_checks.py` y `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` confirman `1 file would be reformatted` en cada archivo, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py` pasa (`18 passed`), por lo que se materializa `RCDX-036` como siguiente `TODO` atomica.

### RCDX-036 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/ruff_checks.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `scripts/quality_gate_components/ruff_checks.py`.
- **alcance permitido**:
  - ajustar unicamente `scripts/quality_gate_components/ruff_checks.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere el loteo ni el diagnostico de version de Ruff del quality gate,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambios funcionales en `scripts/quality_gate_components/ruff_checks.py`,
  - reformatear `scripts/quality_gate_components/toolchain.py` en esta misma ejecucion,
  - cambios en otros scripts del quality gate o en la documentacion fuera del area de checks Ruff.
- **archivos o zonas probables**:
  - `scripts/quality_gate_components/ruff_checks.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ruff_checks.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `scripts/quality_gate_components/ruff_checks.py` deja de aparecer en `ruff format --check`,
  - `tests/test_quality_gate_ruff.py` y `tests/test_quality_gate_ruff_batching.py` siguen en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 15:53:14Z: tras validar `RCDX-035`, `python -m scripts.gate_pr` ya no falla por la suite de `toolchain` y ahora aborta por deuda real de formato en `scripts/quality_gate_components/ruff_checks.py` y `scripts/quality_gate_components/toolchain.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ruff_checks.py` y `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` confirman `1 file would be reformatted` en cada archivo, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`31 passed`). Al no haber evidencia nueva de bug critico ni tests en rojo en el area de Ruff, corresponde atacar primero `scripts/quality_gate_components/ruff_checks.py` por orden del diff antes de retomar `scripts/quality_gate_components/toolchain.py` en una ejecucion posterior. Revalidacion 2026-03-27 16:13:42Z: `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/ruff_checks.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_quality_gate_ruff.py tests/test_quality_gate_ruff_batching.py` pasa (`18 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `scripts/quality_gate_components/toolchain.py`; `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` confirma `1 file would be reformatted` y `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`13 passed`), por lo que se materializa `RCDX-037` como siguiente `TODO` atomica.

### RCDX-037 - Corregir el formateo Ruff pendiente en scripts/quality_gate_components/toolchain.py
- **estado**: BLOCKED
- **objetivo**: Eliminar el bloqueo actual de `python -m scripts.gate_pr` corrigiendo solo el formato pendiente que Ruff reporta en `scripts/quality_gate_components/toolchain.py`.
- **alcance permitido**:
  - ajustar unicamente `scripts/quality_gate_components/toolchain.py` para que pase `ruff format --check`,
  - verificar que el cambio sea solo de formato y no altere la resolucion del interprete esperado ni la lectura del lock dev,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - cambios funcionales en `scripts/quality_gate_components/toolchain.py`,
  - retoques adicionales en `scripts/quality_gate_components/ruff_checks.py` ya revalidado,
  - cambios en otros scripts del quality gate o en la documentacion fuera del area de toolchain.
- **archivos o zonas probables**:
  - `scripts/quality_gate_components/toolchain.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `scripts/quality_gate_components/toolchain.py` deja de aparecer en `ruff format --check`,
  - `tests/test_toolchain_diagnostico.py`, `tests/test_entorno_python.py` y `tests/test_gate_pr.py` siguen en verde sin cambios de contrato,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 16:13:42Z: tras validar `RCDX-036`, `python -m scripts.gate_pr` ya no falla por `scripts/quality_gate_components/ruff_checks.py` y ahora aborta por deuda real de formato en `scripts/quality_gate_components/toolchain.py`. `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` confirma `1 file would be reformatted`, el diff de Ruff del gate completo acota el cambio a partir la comprension de `faltantes` dentro de `_leer_versiones_lock(...)`, y `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`13 passed`). Al no haber evidencia nueva de bug critico ni tests en rojo en el area de toolchain, corresponde atacar este archivo en la siguiente ejecucion atomica. Revalidacion 2026-03-27 16:34:47Z: `.\.venv\Scripts\python.exe -m ruff format --check scripts/quality_gate_components/toolchain.py` queda en verde (`1 file already formatted`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_toolchain_diagnostico.py tests/test_entorno_python.py tests/test_gate_pr.py` pasa (`13 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` avanza mas alla del archivo objetivo y ahora aborta por deuda real de formato en `tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py`. La prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_entrenamiento_handlers.py` falla en tres tests con `TypeError: object.__new__(PagePrediccionAusencias) is not safe, use PagePrediccionAusencias.__new__()`, mientras `.\.venv\Scripts\python.exe -m ruff format --check tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` confirma `1 file would be reformatted`, `.\.venv\Scripts\python.exe -m pytest -q tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` pasa (`3 passed`) y `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_prediccion_ausencias_coordinador_entrenamiento.py` pasa (`4 passed`), por lo que se materializa `RCDX-038` como siguiente `TODO` atomica antes de retomar el formateo del guardrail.

### RCDX-038 - Alinear tests/test_prediccion_ausencias_page_entrenamiento_handlers.py con la inicializacion segura de PagePrediccionAusencias
- **estado**: BLOCKED
- **objetivo**: Corregir la regresion de `tests/test_prediccion_ausencias_page_entrenamiento_handlers.py` que intenta construir `PagePrediccionAusencias` con `object.__new__` y falla en este entorno Python antes de retomar la siguiente deuda de formato del guardrail de prediccion.
- **alcance permitido**:
  - ajustar unicamente `tests/test_prediccion_ausencias_page_entrenamiento_handlers.py` y, si hace falta para no duplicar setup, reutilizar una via de construccion segura compatible con `QWidget`,
  - validar los handlers `_on_entrenar_click`, `_on_entrenar_ok` y `_on_entrenar_fail` sin introducir cambios funcionales de producto en `PagePrediccionAusencias`,
  - mantener intactos `clinicdesk/app/pages/prediccion_ausencias/page.py` y `tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` salvo evidencia nueva adicional,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - reformatear `tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` en esta misma ejecucion,
  - cambios funcionales en `clinicdesk/app/pages/prediccion_ausencias/page.py` sin evidencia nueva de defecto productivo,
  - cambios en otros coordinadores, dialogs o modulos de prediccion.
- **archivos o zonas probables**:
  - `tests/test_prediccion_ausencias_page_entrenamiento_handlers.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_entrenamiento_handlers.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_prediccion_ausencias_coordinador_entrenamiento.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `tests/test_prediccion_ausencias_page_entrenamiento_handlers.py` pasa en este entorno Windows/Python actual,
  - la suite deja de depender de `object.__new__(PagePrediccionAusencias)` y valida los handlers con una construccion segura del widget o de su instancia minima,
  - `tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` y `tests/ui/test_prediccion_ausencias_coordinador_entrenamiento.py` siguen en verde sin cambios funcionales de producto,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 16:34:47Z: tras validar `RCDX-037`, `python -m scripts.gate_pr` pasa a fallar por deuda real de formato en `tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py`, pero la prioridad real cambia porque `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_entrenamiento_handlers.py` falla en `test_on_entrenar_click_no_duplica_arranque_si_running`, `test_on_entrenar_ok_refresca_componentes_clave` y `test_on_entrenar_fail_normaliza_reason_code` con `TypeError: object.__new__(PagePrediccionAusencias) is not safe, use PagePrediccionAusencias.__new__()`. En paralelo, `.\.venv\Scripts\python.exe -m ruff format --check tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` confirma `1 file would be reformatted`, mientras `.\.venv\Scripts\python.exe -m pytest -q tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` pasa (`3 passed`) y `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_prediccion_ausencias_coordinador_entrenamiento.py` pasa (`4 passed`). Por prioridad contractual, primero debe alinearse la suite de handlers con una inicializacion segura antes de retomar la deuda de Ruff del guardrail. Revalidacion 2026-03-27 20:14:48Z: `.\.venv\Scripts\python.exe -m pytest -q tests/test_prediccion_ausencias_page_entrenamiento_handlers.py` pasa (`3 passed`) tras reemplazar `object.__new__(PagePrediccionAusencias)` por `PagePrediccionAusencias.__new__(PagePrediccionAusencias)` con `QApplication` minima y ajustar la expectativa de `_on_entrenar_ok(...)` para incluir `_actualizar_resumen_modelo()`. `.\.venv\Scripts\python.exe -m pytest -q tests/guardrails/test_prediccion_ausencias_page_entrenamiento_job_manager_ast.py` pasa (`3 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_prediccion_ausencias_coordinador_entrenamiento.py` pasa (`4 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` aborta antes del resto del backlog porque `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` detecta `data\clinicdesk.db` y `data\clinicdesk.sqlite`. Como esos binarios locales quedan fuera del alcance permitido de esta tarea, el cierre contractual obligatorio es `BLOCKED` hasta revalidar el gate completo en un workspace sin esos artefactos.

### RCDX-039 - Restablecer la apertura de MainWindow tras login valido
- **estado**: BLOCKED
- **objetivo**: Corregir el fallo productivo que impide entrar en la app con credenciales validas porque `MainWindow.__init__()` referencia `self._on_csv_imported` antes de que exista, provocando `AttributeError` y abortando la transicion post-login.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/ui/main_window.py` y los tests estrictamente necesarios para reintroducir un callback CSV valido compatible con el comportamiento historico de refresco post-importacion,
  - validar que `MainWindow` vuelva a construirse y mostrarse tras un login correcto sin tocar la logica de autenticacion o de persistencia,
  - mantener intactos `clinicdesk/app/main.py`, `clinicdesk/app/session_controller.py` y `clinicdesk/app/controllers/csv_controller.py` salvo que la evidencia nueva demuestre un defecto adicional inseparable,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - resolver en esta misma ejecucion `RCDX-038` o la deuda de formato pendiente del guardrail AST,
  - refactorizar `MainWindow` mas alla del callback perdido que hoy rompe el arranque,
  - cambios funcionales de CSV ajenos al refresco minimo post-importacion.
- **archivos o zonas probables**:
  - `clinicdesk/app/ui/main_window.py`
  - `tests/test_main_post_login_window_open.py`
  - `tests/test_main_window_csv_refresh.py`
  - `tests/test_producto_final_sin_demo.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_producto_final_sin_demo.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_main_window_csv_refresh.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_main_post_login_window_open.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `MainWindow` vuelve a construirse en este entorno sin lanzar `AttributeError`,
  - el callback CSV queda nuevamente definido y solo refresca paginas ya instanciadas del dominio afectado,
  - `tests/test_producto_final_sin_demo.py`, `tests/test_main_window_csv_refresh.py` y `tests/test_main_post_login_window_open.py` quedan en verde,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 16:50:01Z: `logs/app.log` muestra `auth_login_success`, `auth_login_accepted` y `main_window_create` seguidos de `post_login_transition_fail` al intentar entrar con credenciales validas. Una reproduccion controlada con `QT_QPA_PLATFORM=offscreen` y `.\.venv\Scripts\python.exe` contra `bootstrap_database(...)`, `build_container(...)` y `MainWindow(...)` falla en `clinicdesk/app/ui/main_window.py:91` con `AttributeError: 'MainWindow' object has no attribute '_on_csv_imported'`. El historial del archivo (`git show 75cdf05:clinicdesk/app/ui/main_window.py`) confirma que existia un callback `_on_csv_imported(...)` destinado a refrescar la pagina afectada tras una importacion CSV, por lo que corresponde restaurar ese contrato minimo antes de retomar cualquier deuda previa del backlog tecnico. Revalidacion 2026-03-27 16:55:29Z: la reproduccion controlada ya construye `MainWindow` sin excepcion, `.\.venv\Scripts\python.exe -m pytest -q tests/test_producto_final_sin_demo.py tests/test_main_window_csv_refresh.py tests/test_main_post_login_window_open.py` pasa (`8 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` falla antes del resto del backlog porque `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` detecta el artefacto local `data\clinicdesk.db`. Como ese SQLite es un bloqueo operativo ajeno al fix y no debe manipularse automaticamente en esta ejecucion, el cierre contractual queda en `BLOCKED` hasta revalidar el gate completo en un workspace sin ese binario local.

### RCDX-040 - Corregir layout critico desktop y recuperar modulos operativos bloqueados
- **estado**: BLOCKED
- **objetivo**: Restaurar la usabilidad basica del desktop corrigiendo el scroll vertical ausente en pantallas largas, recolocando los listados que hoy quedan empujados al fondo, sustituyendo el layout por pestañas de `Citas` por un calendario compacto arriba y una lista abajo, y recuperando la carga de `Médicos` y `Personal` en este entorno PySide6.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/ui/main_window.py`, `clinicdesk/app/ui/widgets/estado_pantalla_widget.py`, `clinicdesk/app/pages/citas/page.py`, `clinicdesk/app/pages/medicos/dialogs/medico_form.py`, `clinicdesk/app/pages/personal/dialogs/personal_form.py` y los tests estrictamente necesarios para congelar el comportamiento,
  - introducir un contenedor scrollable en el shell desktop sin romper `MainWindow.stack` ni la navegacion lazy existente,
  - mantener la logica funcional de `PageCitas` y solo reemplazar la presentacion por pestañas por una composicion vertical equivalente que conserve intents, refresh y accionado de lista/calendario,
  - corregir el `import_error` de `Médicos` y `Personal` eliminando la dependencia incompatible de `QPointer` sin modificar reglas de validacion de dominio,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la evidencia nueva.
- **fuera de alcance**:
  - implementar funcionalidad nueva de negocio en `Seguro clínica`,
  - reescribir los flujos CRUD de `Médicos`, `Personal`, `Pacientes` o `Citas` mas alla del layout y de la recuperacion de carga/importacion,
  - resolver en esta misma ejecucion `RCDX-038` o deudas tecnicas ajenas al desktop reportado,
  - tocar artefactos binarios locales o el SQLite `data\clinicdesk.db` para forzar el gate completo.
- **archivos o zonas probables**:
  - `clinicdesk/app/ui/main_window.py`
  - `clinicdesk/app/ui/widgets/estado_pantalla_widget.py`
  - `clinicdesk/app/pages/citas/page.py`
  - `clinicdesk/app/pages/medicos/dialogs/medico_form.py`
  - `clinicdesk/app/pages/personal/dialogs/personal_form.py`
  - `tests/test_bootstrap_ui_resiliencia.py`
  - `tests/test_estado_pantalla_widget.py`
  - `tests/test_main_window_scroll_layout.py`
  - `tests/ui/test_ruta_critica_desktop_smoke.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_bootstrap_ui_resiliencia.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_estado_pantalla_widget.py tests/test_main_window_scroll_layout.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/ui/test_ruta_critica_desktop_smoke.py tests/ui/test_citas_security_ui.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - la ventana principal ofrece scroll vertical cuando la pagina activa excede el viewport sin romper `window.stack.currentWidget()`,
  - los listados basados en `EstadoPantallaWidget` dejan de renderizarse en la parte baja de la pantalla,
  - `Médicos` y `Personal` vuelven a registrarse sin placeholder por `import_error`,
  - `Citas` deja de depender de pestañas visibles y muestra calendario compacto arriba con lista abajo conservando las interacciones existentes,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Evidencia 2026-03-27 17:15:39Z: el reporte de usuario con capturas muestra ausencia de scrollbar vertical en `Inicio` y `Predicción de ausencias`, la tabla de `Pacientes` anclada al fondo con encabezados truncados, `Citas` todavia con dos pestañas separadas, placeholders en `Médicos` y `Personal`, y `Seguro clínica` percibido como no implementado. La inspeccion estatica confirma que `MainWindow` no envuelve el stack en ningun `QScrollArea`, que `EstadoPantallaWidget` añade el contenido despues de un `stretch`, que `PageCitas` construye la UI con `QTabWidget`, y que `medico_form.py`/`personal_form.py` importan `QPointer` desde `PySide6.QtCore`, origen directo del `cannot import name 'QPointer'` mostrado en pantalla. `Seguro clínica` queda explicitamente fuera de esta tarea y debe materializarse como backlog posterior si no cabe en la ronda. Revalidacion 2026-03-27 17:43:41Z: los cambios de layout, queries y teardown quedan cubiertos por `.\.venv\Scripts\python.exe -m pytest -q tests/test_bootstrap_ui_resiliencia.py tests/test_citas_listado_queries.py tests/test_estado_pantalla_widget.py tests/test_main_window_scroll_layout.py tests/ui/test_estado_pantalla_widget_qt.py tests/ui/test_citas_coordinadores.py tests/ui/test_citas_security_ui.py tests/ui/test_ruta_critica_desktop_smoke.py` (`32 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` aborta antes del resto de checks porque `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` detecta `data\clinicdesk.db` y `data\clinicdesk.sqlite`. Como esos binarios locales quedan fuera del alcance permitido de esta tarea, el cierre contractual obligatorio es `BLOCKED` hasta revalidar el gate completo en un workspace sin esos artefactos.

### RCDX-042 - Hacer verosimil el seed demo para poblar BBDD util en pantallas y ML
- **estado**: BLOCKED
- **objetivo**: Sustituir el dataset demo artificial actual por una siembra reproducible pero verosimil, suficiente para navegar pantallas operativas y probar los flujos ML sin que la BBDD muestre nombres, notas, incidencias o historicos evidentemente falsos o vacios.
- **alcance permitido**:
  - ajustar unicamente `clinicdesk/app/application/demo_data/**`, `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py`, `clinicdesk/app/infrastructure/sqlite/demo_seed/**`, `clinicdesk/app/infrastructure/sqlite/demo_data_seed_helpers.py`, `scripts/ml_cli.py`, `seed_demo_data.py` y los tests estrictamente necesarios para congelar el contrato,
  - introducir catalogos y reglas deterministas mas naturales para personas, agenda, motivos, notas, incidencias, recordatorios y seguimiento operativo ML,
  - poblar los historicos persistidos que hoy dejan pantallas ML sin contenido util (`predicciones_ausencias_log`, `recordatorios_citas`, `ml_acciones_operativas`) siempre que se mantenga la arquitectura actual,
  - resembrar la base local de trabajo sin versionar cambios binarios y actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con evidencia nueva.
- **fuera de alcance**:
  - reescribir las paginas UI o la logica de negocio de prediccion fuera de los datos semilla,
  - tocar `data/*.db`, `data/*.sqlite` o cualquier otro binario como parte del diff versionado final,
  - introducir integraciones externas, faker ad-hoc no versionado o refactors masivos fuera del seed demo.
- **archivos o zonas probables**:
  - `clinicdesk/app/application/demo_data/generator.py`
  - `clinicdesk/app/infrastructure/sqlite/demo_data_seeder.py`
  - `clinicdesk/app/infrastructure/sqlite/demo_data_seed_helpers.py`
  - `clinicdesk/app/infrastructure/sqlite/demo_seed/orchestration.py`
  - `tests/test_demo_data_generator.py`
  - `tests/test_demo_data_seeder_sqlite.py`
  - `tests/test_seed_demo_empty_modules.py`
  - `tests/test_ml_cli_smoke.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_demo_data_generator.py tests/test_demo_data_seeder_sqlite.py tests/test_seed_demo_empty_modules.py`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_ml_cli_smoke.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - el seed demo deja de generar emails/direcciones/notas/motivos claramente sinteticos de placeholder y mantiene reproducibilidad determinista,
  - la siembra produce suficiente variedad de estados e historicos para que pantallas operativas y ML no queden vacias por falta de `recordatorios_citas`, `predicciones_ausencias_log` o `ml_acciones_operativas`,
  - los tests focalizados del generador/seeder quedan en verde,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Materializada 2026-03-27 19:26:01Z a partir del reporte directo de usuario final indicando que el seeder actual "envia datos no naturales". La inspeccion de `clinicdesk/app/application/demo_data/generator.py` confirma el problema con datos de relleno evidentes (`Calle Salud`, dominios `*.demo`, textos ciclicos y una unica incidencia genérica), y la de `clinicdesk/app/queries/citas_queries.py`, `clinicdesk/app/queries/dashboard_gestion_queries.py` y `clinicdesk/app/queries/prediccion_ausencias_resultados_queries.py` confirma que varias vistas esperan historicos persistidos que hoy no se rellenan en el seed demo. Revalidacion 2026-03-27 20:42:53Z: el contrato del generador queda congelado con pruebas que ya exigen emails/direcciones/notas sin placeholders obvios, `clinicdesk/app/infrastructure/sqlite/demo_seed/operational_history.py` rellena `recordatorios_citas`, `predicciones_ausencias_log` y `ml_acciones_operativas`, `.\.venv\Scripts\python.exe -m pytest -q tests/test_demo_data_generator.py tests/test_demo_data_seeder_sqlite.py tests/test_seed_demo_empty_modules.py` pasa (`7 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_ml_cli_smoke.py` pasa (`5 passed`) y `python -m scripts.gate_rapido` devuelve `rc=0`, pero `python -m scripts.gate_pr` vuelve a abortar en `scripts.quality_gate_components.basic_repo_checks.check_forbidden_artifacts` por `data\clinicdesk.db` y `data\clinicdesk.sqlite`. Revalidacion 2026-03-27 20:52:57Z: se completa el recorte previsto con `clinicdesk/app/application/demo_data/catalogos.py`, `clinicdesk/app/infrastructure/sqlite/demo_seed/contexto_agenda_ml.py`, el ajuste de defaults de ventana en `scripts/ml_cli.py` y `seed_demo_data.py`, y una resembra externa real en `C:\Users\arcas\AppData\Local\ClinicDesk\clinicdesk_demo.sqlite` que deja `5000` citas enriquecidas y trazas operativas/ML pobladas; aun asi, como esos binarios locales dentro de `data\` siguen fuera del alcance permitido de esta tarea, el cierre contractual obligatorio permanece en `BLOCKED` hasta revalidar `python -m scripts.gate_pr` en un workspace sin esos artefactos.

### RCDX-041 - Aterrizar una implementacion usable y honesta de Seguro clínica
- **estado**: BLOCKED
- **objetivo**: Decidir y ejecutar una salida coherente para `Seguro clínica`: o completar una version usable del workspace con flujos verificables, o degradarlo temporalmente a placeholder honesto si el modulo sigue sin estar listo para operacion real.
- **alcance permitido**:
  - auditar `clinicdesk/app/pages/seguros/**`, sus registradores y sus contratos de navegacion para determinar si la implementacion actual es operable o solo parcial,
  - ajustar la presentacion, navegacion y mensajes de `Seguro clínica` sin mezclar cambios en otros modulos desktop,
  - actualizar `docs/roadmap_codex.md` y `docs/bitacora_codex.md` con la conclusion verificable.
- **fuera de alcance**:
  - reestructurar `Citas`, `Pacientes`, `Médicos` o `Personal`,
  - introducir vertical slices nuevas de dominio fuera del modulo `seguros`,
  - resolver deuda tecnica del quality gate no relacionada con este workspace.
- **archivos o zonas probables**:
  - `clinicdesk/app/pages/seguros/page.py`
  - `clinicdesk/app/pages/seguros/workspace_layout.py`
  - `clinicdesk/app/pages/seguros/workspace_navegacion.py`
  - `clinicdesk/app/pages/seguros/page_ui_support.py`
  - `docs/roadmap_codex.md`
  - `docs/bitacora_codex.md`
- **checks obligatorios**:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/application/seguros`
  - `.\.venv\Scripts\python.exe -m pytest -q tests/test_bootstrap_ui_resiliencia.py`
  - `python -m scripts.gate_rapido`
  - `python -m scripts.gate_pr`
- **criterios de cierre**:
  - `Seguro clínica` deja de presentarse como modulo incompleto o engañoso para un usuario final,
  - existe evidencia automatizada de que el workspace elegido carga y navega de forma coherente,
  - `python -m scripts.gate_pr` avanza mas alla del bloqueo actual o revela el siguiente bloqueo real con evidencia concreta.
- **dependencias o bloqueo**: Materializada 2026-03-27 17:15:39Z a partir del reporte de usuario que identifica `Seguro clínica` como no implementado de forma usable aun cuando hoy exista una pantalla registrada. Revalidacion 2026-03-27 20:58:07Z: la auditoria y las pruebas confirman que el modulo ya es operable, pero el problema de UX estaba en el arranque del workspace: se quedaba en `preventa` con multiples `"-"` sin hidratar. La correccion abre `cartera` por defecto, ejecuta `refrescar_cartera()` durante la construccion y rellena `estado_comercial`, `renovaciones`, cartera, recomendacion, campanias y postventa con mensajes honestos o datos reales; `.\.venv\Scripts\python.exe -m pytest -q tests/application/seguros` pasa (`55 passed`), `.\.venv\Scripts\python.exe -m pytest -q tests/test_bootstrap_ui_resiliencia.py` pasa (`7 passed`) y una instanciacion real con `QT_QPA_PLATFORM=offscreen` ya muestra `seccion cartera`, `estado comercial: OFERTA_PREPARADA...` y `Sin campañas ejecutables disponibles.`. Aun asi, como `python -m scripts.gate_pr` sigue abortando por `data\clinicdesk.db` y `data\clinicdesk.sqlite`, el cierre contractual obligatorio permanece en `BLOCKED` hasta revalidar el gate completo en un workspace sin esos artefactos.
