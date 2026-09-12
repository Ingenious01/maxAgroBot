import truststore
truststore.inject_into_ssl()

import time

from backend.config import (
    ADMIN_IDS,
    is_developer,
    WELCOME_TEXT,
    CONSENT_BUTTONS,
    CONSENT_ACCEPTED_TEXT,
    CONSENT_DECLINED_TEXT,
    AFTER_CONSENT_BUTTONS,
    ASK_CONTACT_TEXT,
    CONTACT_SAVED_TEXT,
    CONTACT_SKIP_TEXT,
    CONTACT_CANCEL_TEXT,
    MAIN_MENU_TEXT,
    POLICY_URL,
    main_menu_buttons,
)

from backend.storage.storage import (
    add_subscriber,
    load_subscribers,
    update_user,
    set_state,
    get_state,
    get_pending,
    get_lead,
    upsert_lead,
    delete_lead_field,
    reset_user,
)

from backend.bot.contacts import parse_email

from backend.bot.api import (
    get_updates,
    send_message,
    answer_callback,
)


DEV_HEADER = "⚙️ ИНФОРМАЦИЯ ДЛЯ РАЗРАБОТЧИКА ⚙️"

LOGS_ENABLED_FOR = set()
LOG_BUFFER = []
MAX_LOG_LINES = 50


def send_dev_message(chat_id: int, text: str) -> None:
    send_message(
        chat_id,
        f"{DEV_HEADER}\n\n{text}",
    )


def dev_log(text: str) -> None:
    global LOG_BUFFER

    print(text)

    LOG_BUFFER.append(text)

    if len(LOG_BUFFER) > MAX_LOG_LINES:
        LOG_BUFFER = LOG_BUFFER[-MAX_LOG_LINES:]

    for chat_id in list(LOGS_ENABLED_FOR):
        try:
            send_dev_message(chat_id, text)
        except Exception as e:
            print(
                f"[logs] Не удалось отправить лог "
                f"chat_id={chat_id}: {e}"
            )


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


MENU_STUB_TEXT = "Раздел «{title}» пока находится в разработке."


def open_main_menu(
    chat_id: int,
    intro: str | None = None,
    user_id: int | None = None,
) -> None:
    text = intro or MAIN_MENU_TEXT

    send_message(
        chat_id,
        text,
        buttons=main_menu_buttons(),
    )


def send_welcome(chat_id: int) -> None:
    fmt = "markdown" if POLICY_URL else None

    send_message(
        chat_id,
        WELCOME_TEXT,
        buttons=CONSENT_BUTTONS,
        format=fmt,
    )


def confirm_email_buttons() -> list:
    return [
        [
            {
                "type": "callback",
                "text": "Да, всё верно",
                "payload": "contact_confirm",
            }
        ],
        [
            {
                "type": "callback",
                "text": "Нет, ввести заново",
                "payload": "contact_retry",
            }
        ],
        [
            {
                "type": "callback",
                "text": "Отмена",
                "payload": "contact_cancel",
            }
        ],
    ]


def my_data_keyboard(chat_id: int) -> list:
    lead = get_lead(chat_id) or {}
    email = lead.get("email")

    rows = []

    if email:
        rows.append(
            [
                {
                    "type": "callback",
                    "text": f"📧 {email}",
                    "payload": "edit_email",
                }
            ]
        )
        rows.append(
            [
                {
                    "type": "callback",
                    "text": "Изменить email",
                    "payload": "change_email",
                }
            ]
        )
        rows.append(
            [
                {
                    "type": "callback",
                    "text": "Удалить email",
                    "payload": "delete_email",
                }
            ]
        )
    else:
        rows.append(
            [
                {
                    "type": "callback",
                    "text": "➕ Указать email",
                    "payload": "want_email",
                }
            ]
        )

    rows.append(
        [
            {
                "type": "callback",
                "text": "« В меню",
                "payload": "back_main_menu",
            }
        ]
    )

    return rows


def handle_restart(
    chat_id: int,
    user_id: int | None,
) -> None:
    send_dev_message(
        chat_id,
        "Выполняется сброс тестового профиля...",
    )

    dev_log(
        f"[restart] Начат сброс "
        f"chat_id={chat_id} user_id={user_id}"
    )

    try:
        reset_user(chat_id)

        send_dev_message(
            chat_id,
            "Тестовый профиль сброшен.\n\n"
            "Данные регистрации удалены.\n"
            "Роль разработчика сохранена.\n\n"
            "Регистрация начинается заново.",
        )

        dev_log(
            f"[restart] Сброс завершён "
            f"chat_id={chat_id}"
        )

        send_welcome(chat_id)

    except Exception as e:
        dev_log(
            f"[restart] Ошибка сброса "
            f"chat_id={chat_id}: {e}"
        )

        send_dev_message(
            chat_id,
            f"Ошибка при сбросе профиля:\n\n{e}",
        )


def handle_logs(chat_id: int) -> None:
    if chat_id in LOGS_ENABLED_FOR:
        LOGS_ENABLED_FOR.remove(chat_id)

        send_dev_message(
            chat_id,
            "Логи отключены.",
        )

        print(
            f"[logs] Логи отключены "
            f"chat_id={chat_id}"
        )

        return

    LOG_BUFFER.clear()
    LOGS_ENABLED_FOR.add(chat_id)

    send_dev_message(
        chat_id,
        "Логи включены.\n\n"
        "Будут отображаться только новые события.",
    )

    print(
        f"[logs] Логи включены "
        f"chat_id={chat_id}"
    )


def handle_message_created(update: dict) -> None:
    message = update.get("message", {})
    sender = message.get("sender", {})

    user_id = sender.get("user_id")

    chat_id = message.get(
        "recipient",
        {},
    ).get("chat_id")

    text = (
        message.get("body", {}).get("text")
        or ""
    ).strip()

    if not text or chat_id is None:
        return

    if text.lower() == "/logs":
        if not is_developer(user_id):
            return

        handle_logs(chat_id)
        return

    if text.lower() == "/restart":
        if not is_developer(user_id):
            return

        handle_restart(
            chat_id,
            user_id,
        )
        return

    dev_log(
        f"[bot] Сообщение от "
        f"user_id={user_id} "
        f"chat_id={chat_id}: {text!r}"
    )

    if text.lower() in (
        "/start",
        "start",
        "начать",
    ):
        add_subscriber(
            chat_id,
            max_user_id=user_id,
        )

        set_state(
            chat_id,
            None,
        )

        update_user(
            chat_id,
            max_user_id=user_id,
            onboarded=False,
        )

        send_welcome(chat_id)
        return

    if (
        text.startswith("/post")
        and user_id in ADMIN_IDS
    ):
        news_text = text[len("/post"):].strip()

        if not news_text:
            send_message(
                chat_id,
                "Использование: /post текст новости",
            )
            return

        broadcast(news_text)

        send_message(
            chat_id,
            f"Новость разослана "
            f"{len(load_subscribers())} подписчикам.",
        )
        return

    if text == "/whoami":
        send_message(
            chat_id,
            f"Твой user_id: {user_id}\n"
            f"chat_id: {chat_id}",
        )
        return

    state = get_state(chat_id)

    if state in (
        "wait_contact",
        "wait_email",
    ):
        email = parse_email(text)

        if not email:
            send_message(
                chat_id,
                "Не похоже на email. "
                "Пример: name@mail.ru.\n"
                "Попробуйте снова.",
            )
            return

        pending = {
            "email": email,
            "only": "email",
            "user_id": user_id,
        }

        set_state(
            chat_id,
            "wait_confirm",
            pending=pending,
        )

        send_message(
            chat_id,
            f"Проверьте данные:\n\n"
            f"📧 Email: {email}\n\n"
            f"Всё верно?",
            buttons=confirm_email_buttons(),
        )
        return

    send_message(
        chat_id,
        "Не понимаю эту команду. "
        "Напишите /start, чтобы начать.",
    )


def handle_callback(update: dict) -> None:
    callback = update.get("callback", {})

    callback_id = callback.get("callback_id")
    payload = callback.get("payload")

    original_text = (
        update.get("message", {})
        .get("body", {})
        .get("text")
        or callback.get("message", {})
        .get("body", {})
        .get("text")
        or ""
    )

    chat_id = (
        update.get("chat_id")
        or update.get("message", {})
        .get("recipient", {})
        .get("chat_id")
    )

    dev_log(
        f"[callback] chat_id={chat_id} "
        f"payload={payload!r}"
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

    user_id = (
    (callback.get("user") or {}).get("user_id")
    or callback.get("user_id")
    or update.get("user_id")
    or (update.get("user") or {}).get("user_id")
    or (update.get("message") or {}).get("sender", {}).get("user_id")
    )

    if payload == "consent_yes":
        close_buttons("Принято")

        update_user(
            chat_id,
            max_user_id=user_id,
            consent=True,
        )

        try:
            send_message(
                chat_id,
                CONSENT_ACCEPTED_TEXT,
                buttons=AFTER_CONSENT_BUTTONS,
            )

            dev_log(
                "[bot] AFTER_CONSENT отправлено"
            )

        except Exception as e:
            dev_log(
                f"[bot] Ошибка AFTER_CONSENT: {e}"
            )

            send_message(
                chat_id,
                CONSENT_ACCEPTED_TEXT,
            )

        return

    if payload == "consent_no":
        close_buttons("Отклонено")

        update_user(
            chat_id,
            max_user_id=user_id,
            consent=False,
            onboarded=False,
        )

        send_message(
            chat_id,
            CONSENT_DECLINED_TEXT,
        )
        return

    if payload == "want_email":
        close_buttons()

        set_state(
            chat_id,
            "wait_contact",
        )

        send_message(
            chat_id,
            ASK_CONTACT_TEXT,
        )
        return

    if payload == "skip_email":
        close_buttons()

        update_user(
            chat_id,
            max_user_id=user_id,
            consent=True,
            onboarded=True,
        )

        set_state(
            chat_id,
            None,
        )

        open_main_menu(
            chat_id,
            CONTACT_SKIP_TEXT + "\n\n" + MAIN_MENU_TEXT,
            user_id=user_id,
        )
        return

    if payload == "contact_confirm":
        close_buttons("Сохранено")

        pending = get_pending(chat_id) or {}

        upsert_lead(
            chat_id,
            user_id=pending.get("user_id") or user_id,
            email=pending.get("email"),
        )

        update_user(
            chat_id,
            max_user_id=pending.get("user_id") or user_id,
            consent=True,
            onboarded=True,
        )

        set_state(
            chat_id,
            None,
        )

        open_main_menu(
            chat_id,
            CONTACT_SAVED_TEXT + "\n\n" + MAIN_MENU_TEXT,
            user_id=pending.get("user_id") or user_id,
        )
        return

    if payload == "contact_retry":
        close_buttons()

        set_state(
            chat_id,
            "wait_contact",
        )

        send_message(
            chat_id,
            ASK_CONTACT_TEXT,
        )
        return

    if payload == "contact_cancel":
        close_buttons("Отменено")

        set_state(
            chat_id,
            None,
        )
        return

    if payload in (
        "change_email",
        "edit_email",
    ):
        close_buttons()

        set_state(
            chat_id,
            "wait_email",
        )

        send_message(
            chat_id,
            "Введите email:",
        )
        return

    if payload == "delete_email":
        close_buttons()

        delete_lead_field(
            chat_id,
            "email",
        )

        send_message(
            chat_id,
            "Email удалён.",
            buttons=my_data_keyboard(chat_id),
        )
        return

    if payload == "menu_vk":
        close_buttons()

        send_message(
            chat_id,
            "Наш канал во ВКонтакте:",
            buttons=[
                [
                    {
                        "type": "link",
                        "text": "Открыть ВКонтакте",
                        "url": "https://vk.ru/agro_tomsk",
                    }
                ]
            ],
        )
        return

    if payload in MENU_TITLES:
        close_buttons()

        send_message(
            chat_id,
            MENU_STUB_TEXT.format(
                title=MENU_TITLES[payload]
            ),
            buttons=[
                [
                    {
                        "type": "callback",
                        "text": "« В меню",
                        "payload": "back_main_menu",
                    }
                ]
            ],
        )
        return

    if payload == "back_main_menu":
        close_buttons()

        open_main_menu(
            chat_id,
            user_id=user_id,
        )
        return

    close_buttons()

    dev_log(
        f"[callback] Неизвестный payload: "
        f"{payload!r}"
    )


def broadcast(text: str) -> None:
    subscribers = load_subscribers()

    dev_log(
        f"[broadcast] Начата рассылка "
        f"получателям={len(subscribers)}"
    )

    for chat_id in subscribers:
        try:
            send_message(
                chat_id,
                text,
            )
        except Exception as e:
            dev_log(
                f"[bot] Не удалось отправить "
                f"{chat_id}: {e}"
            )


def handle_bot_started(update: dict) -> None:
    chat_id = update.get("chat_id")

    if chat_id is None:
        return

    user_id = update.get("user_id")

    if user_id is None:
        user = update.get("user") or {}
        user_id = user.get("user_id")

    add_subscriber(
        chat_id,
        max_user_id=user_id,
    )

    set_state(
        chat_id,
        None,
    )

    dev_log(
        f"[bot] bot_started "
        f"chat_id={chat_id} "
        f"user_id={user_id}"
    )

    send_welcome(chat_id)


HANDLERS = {
    "bot_started": handle_bot_started,
    "message_created": handle_message_created,
    "message_callback": handle_callback,
}


def main() -> None:
    dev_log(
        "Бот запущен. "
        "Ожидаю события через Long Polling..."
    )

    marker = None

    while True:
        try:
            data = get_updates(
                marker=marker,
                timeout=25,
            )

        except Exception as e:
            dev_log(
                f"[bot] Ошибка при получении "
                f"обновлений: {e}"
            )

            time.sleep(5)
            continue

        marker = data.get(
            "marker",
            marker,
        )

        for update in data.get(
            "updates",
            [],
        ):
            update_type = update.get(
                "update_type"
            )

            handler = HANDLERS.get(
                update_type
            )

            if handler:
                try:
                    handler(update)
                except Exception as e:
                    dev_log(
                        f"[bot] Ошибка в обработчике "
                        f"{update_type}: {e}"
                    )
            else:
                if update_type not in (
                    "bot_stopped",
                    "dialog_cleared",
                ):
                    dev_log(
                        f"[bot] Неизвестный тип события: "
                        f"{update_type}"
                    )


if __name__ == "__main__":
    main()