import json
import os
from config import SUBSCRIBERS_FILE

STATES_FILE = os.path.join(os.path.dirname(__file__), "states.json")
LEADS_FILE = os.path.join(os.path.dirname(__file__), "leads.json")


# --- Подписчики ---

def load_subscribers() -> set:
    if not os.path.exists(SUBSCRIBERS_FILE):
        return set()
    with open(SUBSCRIBERS_FILE, "r", encoding="utf-8") as f:
        try:
            return set(json.load(f))
        except json.JSONDecodeError:
            return set()


def save_subscribers(subscribers: set) -> None:
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(subscribers), f, ensure_ascii=False, indent=2)


def add_subscriber(chat_id: int) -> None:
    subs = load_subscribers()
    if chat_id not in subs:
        subs.add(chat_id)
        save_subscribers(subs)
        print(f"[storage] Новый подписчик: {chat_id} (всего: {len(subs)})")


# --- Состояния диалога ---

def load_states() -> dict:
    if not os.path.exists(STATES_FILE):
        return {}
    with open(STATES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_states(states: dict) -> None:
    with open(STATES_FILE, "w", encoding="utf-8") as f:
        json.dump(states, f, ensure_ascii=False, indent=2)


def set_state(chat_id: int, state: str | None, pending: dict | None = None) -> None:
    states = load_states()
    key = str(chat_id)
    if state is None:
        states.pop(key, None)
    else:
        entry: dict = {"state": state}
        if pending is not None:
            entry["pending"] = pending
        states[key] = entry
    save_states(states)


def get_state(chat_id: int) -> str | None:
    entry = load_states().get(str(chat_id))
    if not entry:
        return None
    if isinstance(entry, str):  # старый формат
        return entry
    return entry.get("state")


def get_pending(chat_id: int) -> dict | None:
    entry = load_states().get(str(chat_id))
    if not entry or isinstance(entry, str):
        return None
    return entry.get("pending")


# --- Лиды (email + phone) ---

def load_leads() -> dict:
    """chat_id(str) -> {email, phone, user_id}"""
    if not os.path.exists(LEADS_FILE):
        return {}
    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}

    # старый формат — список с полем contact
    if isinstance(data, list):
        result = {}
        for item in data:
            cid = str(item.get("chat_id", ""))
            if not cid:
                continue
            contact = item.get("contact") or ""
            email = item.get("email")
            phone = item.get("phone")
            if not email and not phone and contact:
                if "@" in contact:
                    email = contact
                else:
                    phone = contact
            result[cid] = {
                "user_id": item.get("user_id"),
                "email": email,
                "phone": phone,
            }
        return result

    return data


def save_leads(leads: dict) -> None:
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def get_lead(chat_id: int) -> dict | None:
    return load_leads().get(str(chat_id))


def upsert_lead(
    chat_id: int,
    user_id: int | None = None,
    email: str | None = None,
    phone: str | None = None,
) -> dict:
    """
    Обновляет только переданные поля.
    Чтобы очистить поле, передай пустую строку '' — сохранится как None.
    """
    leads = load_leads()
    key = str(chat_id)
    row = leads.get(key, {"email": None, "phone": None, "user_id": None})

    if user_id is not None:
        row["user_id"] = user_id
    if email is not None:
        row["email"] = email or None
    if phone is not None:
        row["phone"] = phone or None

    leads[key] = row
    save_leads(leads)
    print(f"[storage] Лид {key}: email={row.get('email')!r} phone={row.get('phone')!r}")
    return row


def delete_lead_field(chat_id: int, field: str) -> dict | None:
    """field: 'email' | 'phone'. Если оба пустые — запись удаляется."""
    leads = load_leads()
    key = str(chat_id)
    row = leads.get(key)
    if not row:
        return None

    row[field] = None
    if not row.get("email") and not row.get("phone"):
        leads.pop(key, None)
        save_leads(leads)
        return None

    leads[key] = row
    save_leads(leads)
    return row