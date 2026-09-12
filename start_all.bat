@echo off

cd /d D:\WorkSpace\MaxBot

start "MAX Bot" powershell -NoExit -Command "python -m backend.bot.bot"
start "FastAPI" powershell -NoExit -Command "python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000"
start "ngrok" powershell -NoExit -Command "python ngrok_tunnel.py"