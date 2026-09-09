import os
import time
import requests
from backend.config import API_BASE, BOT_TOKEN

HEADERS = {
    "Authorization": BOT_TOKEN,
    "Content-Type": "application/json",
}

# Одна сессия на всё время работы бота
_session = requests.Session()
_session.headers.update(HEADERS)


def get_updates(marker: int | None = None, timeout: int = 30) -> dict:
    params = {"timeout": timeout}
    if marker is not None:
        params["marker"] = marker

    last_error = None
    for attempt in range(5):
        try:
            resp = _session.get(
                f"{API_BASE}/updates",
                params=params,
                timeout=timeout + 15,  # чуть больше server timeout
            )
            if not resp.ok:
                print(f"[api] Ошибка MAX {resp.status_code}: {resp.text}")
                resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError) as e:
            last_error = e
            wait = min(2 ** attempt, 30)  # 1, 2, 4, 8, 16...
            print(f"[api] Обрыв соединения (попытка {attempt + 1}/5): {e}")
            print(f"[api] Жду {wait} сек и пробую снова...")
            time.sleep(wait)
            # пересоздаём сессию — часто помогает после SSLEOF
            _session.close()
            globals()["_session"] = requests.Session()
            _session.headers.update(HEADERS)

    raise last_error


def send_message(
    chat_id: int,
    text: str,
    buttons: list | None = None,
    format: str | None = None,
    attachments: list | None = None,
) -> dict:
    body: dict = {"text": text}
    if format:
        body["format"] = format
    atts = list(attachments or [])
    if buttons:
        atts.append({
            "type": "inline_keyboard",
            "payload": {"buttons": buttons},
        })
    if atts:
        body["attachments"] = atts
    resp = _session.post(
        f"{API_BASE}/messages",
        params={"chat_id": chat_id},
        json=body,
        timeout=15,
    )
    if not resp.ok:
        print(f"[api] Ошибка MAX {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    return resp.json()


def answer_callback(
    callback_id: str,
    notification: str | None = None,
    text: str | None = None,
    remove_keyboard: bool = False,
) -> None:
    """
    Ответ на callback.
    remove_keyboard=True — перезаписывает сообщение без кнопок (старые кнопки пропадают).
    text — новый текст сообщения (если None, лучше передать исходный текст снаружи).
    """
    body: dict = {}
    if notification:
        body["notification"] = notification
    if remove_keyboard or text is not None:
        msg: dict = {}
        if text is not None:
            msg["text"] = text
        if remove_keyboard:
            # пустой список вложений = убрать клавиатуру
            msg["attachments"] = []
        body["message"] = msg
    try:
        _session.post(
            f"{API_BASE}/answers",
            params={"callback_id": callback_id},
            json=body or {},
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"[api] Не удалось ответить на callback: {e}")

def upload_file(path: str) -> str:
    """Загружает файл, возвращает token для attachments."""
    r = _session.post(f"{API_BASE}/uploads", params={"type": "file"}, timeout=30)
    r.raise_for_status()
    upload_url = r.json()["url"]
    with open(path, "rb") as f:
        up = requests.post(
            upload_url,
            headers={"Authorization": BOT_TOKEN},
            files={"data": (os.path.basename(path), f)},
            timeout=120,
        )
    up.raise_for_status()
    data = up.json()
    token = data.get("token")
    if not token:
        raise RuntimeError(f"Не получен token после загрузки: {data}")
    return token


def send_file(chat_id: int, path: str, caption: str = "") -> dict:
    import os
    import time as _time
    if not os.path.isfile(path):
        return send_message(chat_id, f"Файл политики не найден: {os.path.basename(path)}")
    token = upload_file(path)
    # файл может ещё обрабатываться на стороне MAX
    for delay in (1, 2, 3, 5):
        try:
            body = {
                "text": caption or "Политика обработки персональных данных",
                "attachments": [{"type": "file", "payload": {"token": token}}],
            }
            resp = _session.post(
                f"{API_BASE}/messages",
                params={"chat_id": chat_id},
                json=body,
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()
            if "attachment.not.ready" in (resp.text or ""):
                _time.sleep(delay)
                continue
            if not resp.ok:
                print(f"[api] Ошибка MAX {resp.status_code}: {resp.text}")
                resp.raise_for_status()
        except requests.RequestException:
            _time.sleep(delay)
    raise RuntimeError("Не удалось отправить файл политики")