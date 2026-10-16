@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "APP_ROOT=%%~fI"
set "TASK_NAME=KishaniRepairShop-Reports-Daily"
set "LOG_FILE=%APP_ROOT%\logs\report_scheduler.log"
set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

if not exist "%APP_ROOT%\logs" mkdir "%APP_ROOT%\logs" >nul 2>&1

echo Checking scheduled task "%TASK_NAME%"...
"%POWERSHELL%" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command ^
 "$ErrorActionPreference='Stop'; $task=Get-ScheduledTask -TaskName $env:TASK_NAME -ErrorAction Stop; $info=Get-ScheduledTaskInfo -TaskName $env:TASK_NAME -ErrorAction Stop; Write-Output ('TaskName: ' + $task.TaskName); Write-Output ('State: ' + $task.State); Write-Output ('Run As User: ' + $task.Principal.UserId); Write-Output ('Next Run Time: ' + [string]$info.NextRunTime); Write-Output ('Action: ' + (($task.Actions | ForEach-Object { $_.Execute + ' ' + $_.Arguments }) -join ' | '))"
set "QUERY_EXIT=%ERRORLEVEL%"
if not "%QUERY_EXIT%"=="0" (
    echo.
    echo ERROR: Scheduled task "%TASK_NAME%" was not found or cannot be queried.
    echo PowerShell exit code: %QUERY_EXIT%
    echo Scheduler log: "%LOG_FILE%"
    exit /b %QUERY_EXIT%
)

echo.
echo ============================================================
echo Scheduler verification: OK
echo Task: %TASK_NAME%
echo ============================================================
echo.
exit /b 0
