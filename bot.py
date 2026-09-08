import truststore
truststore.inject_into_ssl()

from dotenv import load_dotenv
load_dotenv()

import time
from config import (
    ADMIN_IDS,
    WELCOME_TEXT,
    CONSENT_BUTTONS,
    CONSENT_ACCEPTED_TEXT,
    CONSENT_DECLINED_TEXT,
    AFTER_CONSENT_BUTTONS,
    ASK_CONTACT_TEXT,
    CONTACT_SAVED_TEXT,
    CONTACT_SKIP_TEXT,
    CONTACT_CANCEL_TEXT,
    MAIN_MENU_BUTTONS,
    MAIN_MENU_TEXT,
    MENU_STUB_TEXT,
    POLICY_URL,
)
from storage import (
    add_subscriber,
    load_subscribers,
    set_state,
    get_state,
    get_pending,
    get_lead,
    upsert_lead,
    delete_lead_field,
)
from contacts import parse_email
from api import get_updates, send_message, answer_callback


MENU_TITLES = {
    "menu_about": "О проекте",
    "menu_news": "Новости АПК",
    "menu_events": "Календарь мероприятий",
    "menu_seminars": "Семинары и обучение",
    "menu_consult": "Запись на консультацию",
    "menu_materials": "Полезные материалы",
    "menu_contacts": "Контакты",
    "menu_vk": "Канал ВКонтакте",
}


def open_main_menu(chat_id: int, intro: str | None = None) -> None:
    text = intro or MAIN_MENU_TEXT
    send_message(chat_id, text, buttons=MAIN_MENU_BUTTONS)


def send_welcome(chat_id: int) -> None:
    # markdown нужен, чтобы [текст](url) стал кликабельной ссылкой
    fmt = "markdown" if POLICY_URL else None
    send_message(chat_id, WELCOME_TEXT, buttons=CONSENT_BUTTONS, format=fmt)


def confirm_email_buttons() -> list:
    return [
        [{"type": "callback", "text": "Да, всё верно", "payload": "contact_confirm"}],
        [{"type": "callback", "text": "Нет, ввести заново", "payload": "contact_retry"}],
        [{"type": "callback", "text": "Отмена", "payload": "contact_cancel"}],
    ]


def my_data_keyboard(chat_id: int) -> list:
    lead = get_lead(chat_id) or {}
    email = lead.get("email")
    rows = []
    if email:
        rows.append([{"type": "callback", "text": f"📧 {email}", "payload": "edit_email"}])
        rows.append([{"type": "callback", "text": "Изменить email", "payload": "change_email"}])
        rows.append([{"type": "callback", "text": "Удалить email", "payload": "delete_email"}])
    else:
        rows.append([{"type": "callback", "text": "➕ Указать email", "payload": "want_email"}])
    rows.append([{"type": "callback", "text": "« В меню", "payload": "back_main_menu"}])
    return rows


def handle_bot_started(update: dict) -> None:
    chat_id = update.get("chat_id")
    if chat_id is None:
        return
    add_subscriber(chat_id)
    set_state(chat_id, None)
    send_welcome(chat_id)


def handle_message_created(update: dict) -> None:
    message = update.get("message", {})
    sender = message.get("sender", {})
    user_id = sender.get("user_id")
    chat_id = message.get("recipient", {}).get("chat_id")
    text = (message.get("body", {}).get("text") or "").strip()

    print(f"[bot] Сообщение от user_id={user_id} chat_id={chat_id}: {text!r}")

    if not text or chat_id is None:
        return

    if text.lower() in ("/start", "start", "начать"):
        add_subscriber(chat_id)
        set_state(chat_id, None)
        send_welcome(chat_id)
        return

    if text.startswith("/post") and user_id in ADMIN_IDS:
        news_text = text[len("/post"):].strip()
        if not news_text:
            send_message(chat_id, "Использование: /post текст новости")
            return
        broadcast(news_text)
        send_message(chat_id, f"Новость разослана {len(load_subscribers())} подписчикам.")
        return

    if text == "/whoami":
        send_message(chat_id, f"Твой user_id: {user_id}\nchat_id: {chat_id}")
        return

    state = get_state(chat_id)
    if state in ("wait_contact", "wait_email"):
        email = parse_email(text)
        if not email:
            send_message(
                chat_id,
                "Не похоже на email. Пример: name@mail.ru.\nПопробуйте снова.",
            )
            return
        pending = {"email": email, "only": "email", "user_id": user_id}
        set_state(chat_id, "wait_confirm", pending=pending)
        send_message(
            chat_id,
            f"Проверьте данные:\n\n📧 Email: {email}\n\nВсё верно?",
            buttons=confirm_email_buttons(),
        )
        return

    send_message(chat_id, "Не понимаю эту команду. Напишите /start, чтобы начать.")


def handle_callback(update: dict) -> None:
    callback = update.get("callback", {})
    callback_id = callback.get("callback_id")
    payload = callback.get("payload")
    original_text = (
        update.get("message", {}).get("body", {}).get("text")
        or callback.get("message", {}).get("body", {}).get("text")
        or ""
    )
    chat_id = (
        update.get("chat_id")
        or update.get("message", {}).get("recipient", {}).get("chat_id")
    )

    def close_buttons(note: str | None = None) -> None:
        if not callback_id:
            return
        answer_callback(
            callback_id,
            notification=note,
            text=original_text or None,
            remove_keyboard=True,
        )

    if chat_id is None:
        close_buttons()
        return

    if payload == "consent_yes":
        close_buttons("Принято")
        send_message(chat_id, CONSENT_ACCEPTED_TEXT, buttons=AFTER_CONSENT_BUTTONS)
        return

    if payload == "consent_no":
        close_buttons("Отклонено")
        send_message(chat_id, CONSENT_DECLINED_TEXT)
        return

    if payload == "want_email":
        close_buttons()
        set_state(chat_id, "wait_contact")
        send_message(chat_id, ASK_CONTACT_TEXT)
        return

    if payload == "skip_email":
        close_buttons()
        set_state(chat_id, None)
        open_main_menu(chat_id, CONTACT_SKIP_TEXT + "\n\n" + MAIN_MENU_TEXT)
        return

    if payload == "contact_confirm":
        close_buttons("Сохранено")
        pending = get_pending(chat_id) or {}
        upsert_lead(chat_id, user_id=pending.get("user_id"), email=pending.get("email"))
        set_state(chat_id, None)
        open_main_menu(chat_id, CONTACT_SAVED_TEXT + "\n\n" + MAIN_MENU_TEXT)
        return

    if payload == "contact_retry":
        close_buttons()
        set_state(chat_id, "wait_contact")
        send_message(chat_id, ASK_CONTACT_TEXT)
        return

    if payload == "contact_cancel":
        close_buttons("Отменено")
        set_state(chat_id, None)
        open_main_menu(chat_id, CONTACT_CANCEL_TEXT + "\n\n" + MAIN_MENU_TEXT)
        return

    if payload == "back_main_menu":
        close_buttons()
        open_main_menu(chat_id)
        return

    if payload == "menu_my_data":
        close_buttons()
        lead = get_lead(chat_id) or {}
        email = lead.get("email")
        text = f"Ваш email: {email}" if email else "Email ещё не указан."
        send_message(chat_id, text, buttons=my_data_keyboard(chat_id))
        return

    if payload in ("change_email", "edit_email"):
        close_buttons()
        set_state(chat_id, "wait_email")
        send_message(chat_id, "Введите email:")
        return

    if payload == "delete_email":
        close_buttons()
        delete_lead_field(chat_id, "email")
        send_message(chat_id, "Email удалён.", buttons=my_data_keyboard(chat_id))
        return

    if payload == "menu_vk":
        close_buttons()
        send_message(
            chat_id,
            "Наш канал во ВКонтакте:",
            buttons=[[{"type": "link", "text": "Открыть ВКонтакте", "url": "https://vk.ru/agro_tomsk"}]],
        )
        return

    if payload in MENU_TITLES:
        close_buttons()
        send_message(
            chat_id,
            MENU_STUB_TEXT.format(title=MENU_TITLES[payload]),
            buttons=[[{"type": "callback", "text": "« В меню", "payload": "back_main_menu"}]],
        )
        return

    close_buttons()
    print(f"[bot] Неизвестный callback payload: {payload!r}")


def broadcast(text: str) -> None:
    for cid in load_subscribers():
        try:
            send_message(cid, text)
        except Exception as e:
            print(f"[bot] Не удалось отправить {cid}: {e}")


HANDLERS = {
    "bot_started": handle_bot_started,
    "message_created": handle_message_created,
    "message_callback": handle_callback,
}


def main() -> None:
    print("Бот запущен. Ожидаю события через Long Polling...")
    marker = None
    while True:
        try:
            data = get_updates(marker=marker, timeout=25)
        except Exception as e:
            print(f"[bot] Ошибка при получении обновлений: {e}")
            time.sleep(5)
            continue

        marker = data.get("marker", marker)
        for update in data.get("updates", []):
            update_type = update.get("update_type")
            handler = HANDLERS.get(update_type)
            if handler:
                try:
                    handler(update)
                except Exception as e:
                    print(f"[bot] Ошибка в обработчике {update_type}: {e}")
            else:
                if update_type not in ("bot_stopped", "dialog_cleared"):
                    print(f"[bot] Неизвестный тип события: {update_type}")


if __name__ == "__main__":
    main()