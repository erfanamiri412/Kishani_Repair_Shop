@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem ============================================================
rem KishaniRepairShop - Daily report generation
rem ============================================================

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "APP_ROOT=%%~fI"
for %%I in ("%APP_ROOT%\..") do set "PROJECT_ROOT=%%~fI"

set "MANAGE_PY=%APP_ROOT%\manage.py"
set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
set "LOG_DIR=%APP_ROOT%\logs"
set "LOG_FILE=%LOG_DIR%\report_scheduler.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

>>"%LOG_FILE%" echo.
>>"%LOG_FILE%" echo ============================================================
>>"%LOG_FILE%" echo [%DATE% %TIME%] Daily report generation started
>>"%LOG_FILE%" echo Application root: %APP_ROOT%
>>"%LOG_FILE%" echo Project root: %PROJECT_ROOT%
>>"%LOG_FILE%" echo Python: %PYTHON_EXE%
>>"%LOG_FILE%" echo Manage.py: %MANAGE_PY%

if not exist "%MANAGE_PY%" (
    >>"%LOG_FILE%" echo ERROR: manage.py not found: %MANAGE_PY%
    exit /b 2
)

if not exist "%PYTHON_EXE%" (
    >>"%LOG_FILE%" echo ERROR: Python not found: %PYTHON_EXE%
    exit /b 3
)

pushd "%APP_ROOT%" >nul 2>&1
if errorlevel 1 (
    >>"%LOG_FILE%" echo ERROR: Could not change directory to %APP_ROOT%
    exit /b 4
)

"%PYTHON_EXE%" "%MANAGE_PY%" generate_reports >>"%LOG_FILE%" 2>&1
set "REPORT_EXIT=%ERRORLEVEL%"
popd

if not "%REPORT_EXIT%"=="0" (
    >>"%LOG_FILE%" echo ERROR: generate_reports failed with exit code %REPORT_EXIT%
    exit /b %REPORT_EXIT%
)

>>"%LOG_FILE%" echo [%DATE% %TIME%] Daily report generation completed successfully.
exit /b 0
