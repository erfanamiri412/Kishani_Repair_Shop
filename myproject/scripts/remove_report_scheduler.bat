@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "APP_ROOT=%%~fI"
set "TASK_NAME=KishaniRepairShop-Reports-Daily"
set "LOG_DIR=%APP_ROOT%\logs"
set "LOG_FILE=%LOG_DIR%\report_scheduler.log"
set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "FLTMCR=%SystemRoot%\System32\fltmc.exe"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

"%FLTMCR%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Administrator privileges are required.
    echo Open Command Prompt with Run as administrator and run:
    echo   scripts\remove_report_scheduler.bat
    exit /b 1
)

"%POWERSHELL%" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command ^
 "$ErrorActionPreference='Stop'; $task=Get-ScheduledTask -TaskName $env:TASK_NAME -ErrorAction SilentlyContinue; if ($null -eq $task) { Write-Output 'NOT_FOUND'; exit 0 }; Unregister-ScheduledTask -TaskName $env:TASK_NAME -Confirm:$false -ErrorAction Stop; Write-Output 'REMOVED'"
set "PS_EXIT=%ERRORLEVEL%"

if not "%PS_EXIT%"=="0" (
    echo ERROR: Could not remove task "%TASK_NAME%". PowerShell exit code: %PS_EXIT%
    exit /b %PS_EXIT%
)

>>"%LOG_FILE%" echo [%DATE% %TIME%] Scheduler removed or was already absent.
echo Scheduler "%TASK_NAME%" removed successfully (or was already absent).
exit /b 0
