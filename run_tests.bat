@echo off
setlocal

if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
) else (
  echo [ClinicDesk] Aviso: no se encontro .venv. Usando Python del sistema.
)

python -m clinicdesk.tools.test_launcher
set EXITCODE=%ERRORLEVEL%

endlocal & exit /b %EXITCODE%
