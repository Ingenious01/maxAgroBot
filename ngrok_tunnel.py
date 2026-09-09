import os

import ngrok
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("NGROK_AUTHTOKEN"):
    raise RuntimeError("Не задан NGROK_AUTHTOKEN в .env")

tunnel = ngrok.forward(
    "localhost:8000",
    authtoken_from_env=True,
)

print(f"Публичный адрес: {tunnel.url()}")

input("Нажмите Enter для остановки туннеля...")