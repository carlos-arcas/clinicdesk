@echo off
setlocal

cd /d "%~dp0\.."
python scripts\setup.py

endlocal & exit /b %ERRORLEVEL%
