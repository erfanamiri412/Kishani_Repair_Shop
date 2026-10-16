@echo off
setlocal
cd /d "%~dp0myproject"
call "%~dp0.venv\Scripts\activate.bat"
if errorlevel 1 exit /b 1
python manage.py run_maintenance_cycle --limit 100
endlocal
