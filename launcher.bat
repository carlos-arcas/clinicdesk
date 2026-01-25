@echo off
setlocal EnableExtensions

REM Ir al directorio del propio .bat (raíz del repo)
cd /d "%~dp0"

REM Activar venv si existe
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo [WARN] No existe .venv. Ejecutando con el Python del sistema...
)

REM Ejecutar la app por modulo (estable con paquetes)
python -m clinicdesk.app.main

REM Si falla, pausa para ver el error al hacer doble click
if errorlevel 1 pause
endlocal