import os
from dotenv import load_dotenv


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

load_dotenv(
    os.path.join(PROJECT_ROOT, ".env")
)

BOT_TOKEN = os.environ.get("MAX_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "Не задан MAX_BOT_TOKEN. "
        "Создай файл .env с MAX_BOT_TOKEN=... или в PowerShell: "
        '$env:MAX_BOT_TOKEN=\"токен\"; python bot.py'
    )

# Администраторы
ADMIN_IDS = {
    236862264,
    339836365,
}

# Разработчики
DEVELOPER_IDS = {
    339836365,  # временно для тестирования
}

DB_SERVER = os.environ.get("DB_SERVER", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "1433"))
DB_NAME = os.environ.get("DB_NAME", "MaxBot")
DB_DRIVER = os.environ.get(
    "DB_DRIVER",
    "ODBC Driver 17 for SQL Server",
)
DB_TRUSTED_CONNECTION = (
    os.environ.get("DB_TRUSTED_CONNECTION", "yes").lower() == "yes"
)
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")


def is_admin(user_id: int | None) -> bool:
    return user_id in ADMIN_IDS


def is_developer(user_id: int | None) -> bool:
    return user_id in DEVELOPER_IDS or user_id in ADMIN_IDS

API_BASE = "https://platform-api2.max.ru"

SUBSCRIBERS_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "subscribers.json"
)

POLICY_URL = os.environ.get(
    "POLICY_URL",
    "https://store.steampowered.com/?l=russian",  # потом замени на реальную политику
)

PRIVACY_POLICY_FILE = os.path.join(
    PROJECT_ROOT,
    "webapp",
    "privacy_policy.pdf"
)

MINIAPP_URL = os.environ.get(
    "MINIAPP_URL",
    "https://ingenious01.github.io/maxAgroBot/",
)

if POLICY_URL:
    _policy_phrase = f"[условия политики обработки персональных данных]({POLICY_URL})"
else:
    _policy_phrase = "условия политики обработки персональных данных"

WELCOME_TEXT = (
    "Здравствуйте! 🌾 Рады приветствовать Вас в чат-боте «Томский агробизнес». "
    "Бот помогает представителям малого агробизнеса быть в курсе свежих новостей, "
    "записаться на мероприятие или личную консультацию.\n\n"
    f"Чтобы продолжить взаимодействие с ботом, необходимо принять {_policy_phrase}."
)

CONSENT_BUTTONS = [
    [{"type": "callback", "text": "Подтвердить", "payload": "consent_yes"}],
    [{"type": "callback", "text": "Отказаться", "payload": "consent_no"}],
]

CONSENT_ACCEPTED_TEXT = (
    "Рад, что вы с нами! 🌿\n\n"
    "Можно оставить email для анонсов и персональных рекомендаций — "
    "или пропустить этот шаг и перейти в меню."
)

CONSENT_DECLINED_TEXT = (
    "Жаль, что Вы не с нами. Если хотите изменить своё решение, напишите /start"
)

ASK_CONTACT_TEXT = (
    "Оставьте, пожалуйста, ваш email 📩\n"
    "На него будем присылать анонсы и полезные материалы."
)

CONTACT_SAVED_TEXT = "Спасибо! Email сохранён. 🎉"

CONTACT_SKIP_TEXT = "Хорошо, продолжаем без email."

CONTACT_CANCEL_TEXT = "Хорошо, данные не сохранены."

VK_BUTTON = {
    "type": "link",
    "text": "Перейти в канал ВКонтакте",
    "url": "https://vk.ru/agro_tomsk",
}

AFTER_CONSENT_BUTTONS = [
    [{"type": "callback", "text": "Хочу получать анонсы на почту", "payload": "want_email"}],
    [{"type": "callback", "text": "Пропустить", "payload": "skip_email"}],
    [VK_BUTTON],
]

MAIN_MENU_TEXT = (
    "Готово! 🌾\n\n"
    "Основная работа с ботом ведётся через встроенное приложение MAX.\n\n"
    "Нажмите кнопку ниже, чтобы открыть приложение."
)


def main_menu_buttons() -> list:
    return [[
        {
            "type": "open_app",
            "text": "Открыть приложение",
            "web_app": "id7017234465_bot",
        }
    ]]