@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem ============================================================
rem KishaniRepairShop - Install report scheduler
rem ============================================================

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "APP_ROOT=%%~fI"
for %%I in ("%APP_ROOT%\..") do set "PROJECT_ROOT=%%~fI"

set "TASK_NAME=KishaniRepairShop-Reports-Daily"
set "DAILY_SCRIPT=%APP_ROOT%\scripts\generate_reports_daily.bat"
set "MANAGE_PY=%APP_ROOT%\manage.py"
set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
set "LOG_DIR=%APP_ROOT%\logs"
set "LOG_FILE=%LOG_DIR%\report_scheduler.log"
set "POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "FLTMCR=%SystemRoot%\System32\fltmc.exe"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

"%FLTMCR%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Administrator privileges are required.
    echo Open Command Prompt with Run as administrator and run:
    echo   scripts\install_report_scheduler.bat
    exit /b 1
)

if not exist "%MANAGE_PY%" (
    echo ERROR: manage.py not found:
    echo "%MANAGE_PY%"
    exit /b 2
)

if not exist "%DAILY_SCRIPT%" (
    echo ERROR: daily scheduler script not found:
    echo "%DAILY_SCRIPT%"
    exit /b 3
)

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python virtual environment not found:
    echo "%PYTHON_EXE%"
    exit /b 4
)

>>"%LOG_FILE%" echo.
>>"%LOG_FILE%" echo ============================================================
>>"%LOG_FILE%" echo [%DATE% %TIME%] Installing report scheduler
>>"%LOG_FILE%" echo Application root: %APP_ROOT%
>>"%LOG_FILE%" echo Project root: %PROJECT_ROOT%
>>"%LOG_FILE%" echo Task name: %TASK_NAME%
>>"%LOG_FILE%" echo Manage.py: %MANAGE_PY%
>>"%LOG_FILE%" echo Python: %PYTHON_EXE%
>>"%LOG_FILE%" echo Daily script: %DAILY_SCRIPT%
>>"%LOG_FILE%" echo First run: tomorrow at 00:10
>>"%LOG_FILE%" echo Run as: NT AUTHORITY\SYSTEM

rem The ScheduledTasks PowerShell API is used here instead of schtasks.exe.
rem This avoids locale-dependent /sd parsing and fragile /tr quoting.
"%POWERSHELL%" -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command ^
 "$ErrorActionPreference='Stop'; Import-Module ScheduledTasks -ErrorAction Stop; $taskName=$env:TASK_NAME; $q=[char]34; $actionArgs='/d /c call ' + $q + $env:DAILY_SCRIPT + $q; $action=New-ScheduledTaskAction -Execute $env:ComSpec -Argument $actionArgs -WorkingDirectory $env:APP_ROOT; $firstRun=(Get-Date).Date.AddDays(1).AddMinutes(10); $trigger=New-ScheduledTaskTrigger -Daily -At $firstRun; $principal=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest; $settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null; $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop; $info=Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction Stop; Write-Output ('TASK_NAME=' + $task.TaskName); Write-Output ('STATE=' + $task.State); Write-Output ('RUN_AS=' + $task.Principal.UserId); Write-Output ('NEXT_RUN=' + [string]$info.NextRunTime); Write-Output 'RESULT=OK'" >>"%LOG_FILE%" 2>&1
set "PS_EXIT=%ERRORLEVEL%"

if not "%PS_EXIT%"=="0" (
    echo ERROR: Windows Task Scheduler registration failed.
    echo PowerShell exit code: %PS_EXIT%
    echo Detailed error written to:
    echo "%LOG_FILE%"
    echo.
    type "%LOG_FILE%"
    exit /b 7
)

findstr /C:"RESULT=OK" "%LOG_FILE%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Scheduler registration did not report RESULT=OK.
    echo Review: "%LOG_FILE%"
    exit /b 8
)

echo.
echo ============================================================
echo Report scheduler installed successfully.
echo Task: %TASK_NAME%
echo First run: tomorrow at 00:10
echo Daily: every day at 00:10
echo Run as: NT AUTHORITY\SYSTEM
echo Python: %PYTHON_EXE%
echo Log: %LOG_FILE%
echo ============================================================
echo.
exit /b 0
