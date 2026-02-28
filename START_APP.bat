@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "CLINICDESK_DB_PATH=%CD%\data\clinicdesk.db"
set "PYTHONPATH=."

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m clinicdesk.app.main
) else (
    python -m clinicdesk.app.main
)

endlocal
exit /b %ERRORLEVEL%
