import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import BOT_TOKEN
from backend.storage.database import engine

from sqlalchemy import text


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class AuthRequest(BaseModel):
    initData: str


def validate_init_data(init_data: str) -> dict:
    if not init_data:
        raise ValueError("Пустой initData")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = pairs.pop("hash", None)

    if not received_hash:
        raise ValueError("В initData отсутствует hash")

    auth_date_raw = pairs.get("auth_date")

    if not auth_date_raw:
        raise ValueError("В initData отсутствует auth_date")

    try:
        auth_date = int(auth_date_raw)
    except ValueError:
        raise ValueError("Некорректный auth_date")

    current_time = int(time.time())

    if current_time - auth_date > 3600:
        raise ValueError("Срок действия initData истёк")

    if auth_date - current_time > 60:
        raise ValueError("Некорректное время auth_date")

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(pairs.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        calculated_hash,
        received_hash,
    ):
        raise ValueError("Неверная подпись initData")

    user_raw = pairs.get("user")

    if not user_raw:
        raise ValueError("В initData отсутствует user")

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        raise ValueError("Некорректные данные user")

    user_id = user.get("id")

    if not user_id:
        raise ValueError("В данных пользователя отсутствует id")

    return {
        "user_id": int(user_id),
        "user": user,
        "chat_id": (
            int(pairs["chat_id"])
            if pairs.get("chat_id")
            else None
        ),
        "start_param": pairs.get("start_param"),
    }


def check_user_access(user_id: int) -> bool:
    with engine.connect() as connection:
        row = connection.execute(
            text("""
                SELECT
                    Consent,
                    Onboarded
                FROM app.Users
                WHERE MaxUserId = :user_id
            """),
            {
                "user_id": user_id,
            },
        ).mappings().first()

    if not row:
        return False

    return (
        bool(row["Consent"])
        and bool(row["Onboarded"])
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
    }


@app.post("/api/auth")
def authenticate(request: AuthRequest):
    try:
        auth = validate_init_data(
            request.initData
        )

        allowed = check_user_access(
            auth["user_id"]
        )

        return {
            "authenticated": True,
            "allowed": allowed,
            "user_id": auth["user_id"],
        }

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )

    except Exception as e:
        print(
            f"[api] Ошибка авторизации Mini App: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера",
        )