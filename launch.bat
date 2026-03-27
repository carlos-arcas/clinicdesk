@echo off
setlocal EnableExtensions

cd /d "%~dp0"

if not exist "launcher.bat" (
    echo [ERROR] No se encuentra launcher.bat
    endlocal & exit /b 1
)

call "launcher.bat"
set "APP_EXIT=%ERRORLEVEL%"

endlocal & exit /b %APP_EXIT%
