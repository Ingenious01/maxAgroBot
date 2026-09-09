import re

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 10:
        return None
    # 8XXXXXXXXXX → 7XXXXXXXXXX
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if not (len(digits) == 11 and digits.startswith("7")):
        return None
    return "+" + digits


def parse_email(text: str) -> str | None:
    m = EMAIL_RE.search(text.strip())
    return m.group(0).lower() if m else None


def format_contacts_preview(email: str | None, phone: str | None) -> str:
    lines = []
    if email:
        lines.append(f"📧 Email: {email}")
    if phone:
        lines.append(f"📱 Телефон: {phone}")
    return "\n".join(lines) if lines else "Ничего не распознано."