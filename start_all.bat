@echo off

cd /d "%~dp0"

if /I "%~1"=="stop" goto stop

powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'backend\.bot\.bot' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'backend\.api\.main:app' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'ngrok_tunnel\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

powershell -NoProfile -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -in @('MAX Bot','FastAPI','ngrok') } | Stop-Process -Force -ErrorAction SilentlyContinue"

timeout /t 1 /nobreak >nul

start "MAX Bot" powershell -NoExit -Command "python -m backend.bot.bot"
start "FastAPI" powershell -NoExit -Command "python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000"
start "ngrok" powershell -NoExit -Command "python ngrok_tunnel.py"

exit /b

:stop

powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'backend\.bot\.bot' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'backend\.api\.main:app' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'ngrok_tunnel\.py' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

powershell -NoProfile -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -in @('MAX Bot','FastAPI','ngrok') } | Stop-Process -Force -ErrorAction SilentlyContinue"