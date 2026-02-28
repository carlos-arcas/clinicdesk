@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "CLINICDESK_DB_PATH=%CD%\data\clinicdesk.db"
set "PYTHONPATH=."

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" seed_demo_data.py --seed 123 --doctors 25 --patients 500 --appointments 5000 --from 2025-01-01 --to 2026-02-28 --incidence-rate 0.15 --sqlite-path "%CLINICDESK_DB_PATH%" --reset
) else (
    python seed_demo_data.py --seed 123 --doctors 25 --patients 500 --appointments 5000 --from 2025-01-01 --to 2026-02-28 --incidence-rate 0.15 --sqlite-path "%CLINICDESK_DB_PATH%" --reset
)

endlocal
exit /b %ERRORLEVEL%
