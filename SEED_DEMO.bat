@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo ============================================
echo Generador de datos demo (ClinicDesk)
echo Carpeta: %CD%
echo ============================================

if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    echo [INFO] Entorno virtual activado: .venv
) else (
    echo [WARN] No existe .venv. Se usara Python del sistema.
)

set "PYTHONPATH=."
python seed_demo_data.py --seed 123 --doctors 25 --patients 500 --appointments 5000 --from 2025-01-01 --to 2026-02-28 --incidence-rate 0.15 --sqlite-path .\data\demo.db --reset
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo la generacion de datos demo.
    pause
    endlocal
    exit /b 1
)

echo.
echo Datos demo generados.
pause
endlocal
exit /b 0
