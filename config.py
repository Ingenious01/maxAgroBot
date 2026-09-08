import os

BOT_TOKEN = os.environ.get("MAX_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "Не задан MAX_BOT_TOKEN. "
        "Создай файл .env с MAX_BOT_TOKEN=... или в PowerShell: "
        '$env:MAX_BOT_TOKEN=\"токен\"; python bot.py'
    )

ADMIN_IDS = [
    236862264,
    339836365,
]

API_BASE = "https://platform-api2.max.ru"

SUBSCRIBERS_FILE = os.path.join(os.path.dirname(__file__), "subscribers.json")

POLICY_URL = os.environ.get(
    "POLICY_URL",
    "https://store.steampowered.com/?l=russian",  # потом замени на реальную политику
)

PRIVACY_POLICY_FILE = os.path.join(os.path.dirname(__file__), "privacy_policy.pdf")

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

CONTACT_SAVED_TEXT = (
    "Спасибо! Email сохранён. 🎉\n"
    "Открываю главное меню."
)

CONTACT_SKIP_TEXT = "Хорошо, продолжаем без email. Открываю главное меню."

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

MAIN_MENU_TEXT = "📌 Главное меню\n\nВыберите раздел:"

MENU_STUB_TEXT = "Раздел «{title}» пока в разработке. Скоро здесь появится контент."

MAIN_MENU_BUTTONS = [
    [{"type": "callback", "text": "ℹ️ О проекте", "payload": "menu_about"}],
    [{"type": "callback", "text": "📰 Новости АПК", "payload": "menu_news"}],
    [{"type": "callback", "text": "📅 Календарь мероприятий", "payload": "menu_events"}],
    [{"type": "callback", "text": "🎓 Семинары и обучение", "payload": "menu_seminars"}],
    [{"type": "callback", "text": "💬 Запись на консультацию", "payload": "menu_consult"}],
    [{"type": "callback", "text": "📁 Полезные материалы", "payload": "menu_materials"}],
    [{"type": "callback", "text": "📞 Контакты", "payload": "menu_contacts"}],
    [{"type": "callback", "text": "📣 Канал ВКонтакте", "payload": "menu_vk"}],
    [{"type": "callback", "text": "⚙️ Мои данные (email)", "payload": "menu_my_data"}],
]