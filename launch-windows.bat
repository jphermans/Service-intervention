@echo off
setlocal enableextensions

set "SCRIPT_DIR=%~dp0"
set "PORT=%INTERVENTION_PORT%"
if not defined PORT set "PORT=8000"
set "NO_BROWSER="

:parse_args
if "%~1"=="" goto run
if /I "%~1"=="--no-browser" (
    set "NO_BROWSER=1"
    shift
    goto parse_args
)
for /f "delims=0123456789" %%A in ("%~1") do (
    echo Unknown argument: %~1
    echo Usage: %~n0 [port] [--no-browser]
    exit /b 1
)
set "PORT=%~1"
shift
goto parse_args

:run
if defined NO_BROWSER (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%launch-windows.ps1" -Port %PORT% -NoBrowser
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%launch-windows.ps1" -Port %PORT%
)
exit /b %errorlevel%
