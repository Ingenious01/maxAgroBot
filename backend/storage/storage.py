import json

from sqlalchemy import text

from backend.storage.database import engine

def _get_user_row(chat_id: int):
    """
    Возвращает пользователя из app.Users по ChatId.
    """
    with engine.connect() as connection:
        return connection.execute(
            text("""
                SELECT
                    Id,
                    MaxUserId,
                    ChatId,
                    Role,
                    Consent,
                    Onboarded
                FROM app.Users
                WHERE ChatId = :chat_id
            """),
            {
                "chat_id": chat_id,
            },
        ).mappings().first()


def ensure_user(
    chat_id: int,
    max_user_id: int | None = None,
) -> dict:
    """
    Находит пользователя или создаёт его.

    max_user_id — реальный user_id пользователя MAX.
    Пока он не передан, временно используется chat_id.
    При следующем вызове с реальным max_user_id значение будет исправлено.
    """

    row = _get_user_row(chat_id)

    if row:
        if (
            max_user_id is not None
            and row["MaxUserId"] != max_user_id
        ):
            with engine.begin() as connection:
                connection.execute(
                    text("""
                        UPDATE app.Users
                        SET
                            MaxUserId = :max_user_id,
                            UpdatedAt = SYSUTCDATETIME()
                        WHERE ChatId = :chat_id
                    """),
                    {
                        "chat_id": chat_id,
                        "max_user_id": max_user_id,
                    },
                )

            row = _get_user_row(chat_id)

        return {
            "id": row["Id"],
            "max_user_id": row["MaxUserId"],
            "chat_id": row["ChatId"],
            "role": row["Role"],
            "consent": bool(row["Consent"]),
            "onboarded": bool(row["Onboarded"]),
        }

    real_max_user_id = (
        max_user_id
        if max_user_id is not None
        else chat_id
    )

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO app.Users
                (
                    MaxUserId,
                    ChatId,
                    Role,
                    Consent,
                    Onboarded
                )
                OUTPUT INSERTED.Id
                VALUES
                (
                    :max_user_id,
                    :chat_id,
                    N'user',
                    0,
                    0
                )
            """),
            {
                "max_user_id": real_max_user_id,
                "chat_id": chat_id,
            },
        )

        db_id = result.scalar_one()

    return {
        "id": db_id,
        "max_user_id": real_max_user_id,
        "chat_id": chat_id,
        "role": "user",
        "consent": False,
        "onboarded": False,
    }


def get_user(chat_id: int) -> dict:
    """
    Возвращает данные пользователя.
    Если пользователя нет — возвращает значения по умолчанию.
    """

    row = _get_user_row(chat_id)

    if not row:
        return {
            "consent": False,
            "onboarded": False,
        }

    return {
        "consent": bool(row["Consent"]),
        "onboarded": bool(row["Onboarded"]),
        "role": row["Role"],
        "max_user_id": row["MaxUserId"],
        "chat_id": row["ChatId"],
    }


def update_user(
    chat_id: int,
    max_user_id: int | None = None,
    **fields,
) -> dict:
    """
    Обновляет данные пользователя.

    Поддерживаемые поля:
        consent
        onboarded
        role
    """

    user = ensure_user(
        chat_id,
        max_user_id=max_user_id,
    )

    allowed_fields = {
        "consent",
        "onboarded",
        "role",
    }

    updates = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if updates:
        set_parts = []
        params = {
            "chat_id": chat_id,
        }

        for key, value in updates.items():
            column = {
                "consent": "Consent",
                "onboarded": "Onboarded",
                "role": "Role",
            }[key]

            param_name = f"value_{key}"

            set_parts.append(
                f"{column} = :{param_name}"
            )

            params[param_name] = value

        set_parts.append(
            "UpdatedAt = SYSUTCDATETIME()"
        )

        with engine.begin() as connection:
            connection.execute(
                text(f"""
                    UPDATE app.Users
                    SET
                        {", ".join(set_parts)}
                    WHERE ChatId = :chat_id
                """),
                params,
            )

    return get_user(chat_id)

def set_state(
    chat_id: int,
    state: str | None,
    pending: dict | None = None,
) -> None:
    """
    Устанавливает состояние пользователя.

    pending хранится в NVARCHAR(MAX) как JSON.
    """

    user = ensure_user(chat_id)

    if state is None:
        with engine.begin() as connection:
            connection.execute(
                text("""
                    DELETE FROM app.UserStates
                    WHERE UserId = :user_id
                """),
                {
                    "user_id": user["id"],
                },
            )

        return

    pending_json = None

    if pending is not None:
        pending_json = json.dumps(
            pending,
            ensure_ascii=False,
        )

    with engine.begin() as connection:
        existing = connection.execute(
            text("""
                SELECT Id
                FROM app.UserStates
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["id"],
            },
        ).first()

        if existing:
            connection.execute(
                text("""
                    UPDATE app.UserStates
                    SET
                        State = :state,
                        PendingData = :pending_data,
                        UpdatedAt = SYSUTCDATETIME()
                    WHERE UserId = :user_id
                """),
                {
                    "user_id": user["id"],
                    "state": state,
                    "pending_data": pending_json,
                },
            )
        else:
            connection.execute(
                text("""
                    INSERT INTO app.UserStates
                    (
                        UserId,
                        State,
                        PendingData
                    )
                    VALUES
                    (
                        :user_id,
                        :state,
                        :pending_data
                    )
                """),
                {
                    "user_id": user["id"],
                    "state": state,
                    "pending_data": pending_json,
                },
            )


def get_state(chat_id: int) -> str | None:
    """
    Возвращает текущее состояние пользователя.
    """

    user = _get_user_row(chat_id)

    if not user:
        return None

    with engine.connect() as connection:
        row = connection.execute(
            text("""
                SELECT State
                FROM app.UserStates
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["Id"],
            },
        ).first()

    if not row:
        return None

    return row[0]


def get_pending(chat_id: int) -> dict | None:
    """
    Возвращает временные данные состояния.
    """

    user = _get_user_row(chat_id)

    if not user:
        return None

    with engine.connect() as connection:
        row = connection.execute(
            text("""
                SELECT PendingData
                FROM app.UserStates
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["Id"],
            },
        ).first()

    if not row or not row[0]:
        return None

    try:
        return json.loads(row[0])
    except (TypeError, json.JSONDecodeError):
        return None

def get_lead(chat_id: int) -> dict | None:
    """
    Возвращает email/телефон пользователя.
    """

    user = _get_user_row(chat_id)

    if not user:
        return None

    with engine.connect() as connection:
        row = connection.execute(
            text("""
                SELECT
                    Email,
                    Phone,
                    u.MaxUserId
                FROM app.Contacts c
                INNER JOIN app.Users u
                    ON u.Id = c.UserId
                WHERE c.UserId = :user_id
            """),
            {
                "user_id": user["Id"],
            },
        ).mappings().first()

    if not row:
        return None

    return {
        "email": row["Email"],
        "phone": row["Phone"],
        "user_id": row["MaxUserId"],
    }


def upsert_lead(
    chat_id: int,
    user_id: int | None = None,
    email: str | None = None,
    phone: str | None = None,
) -> dict:
    """
    Создаёт или обновляет контактные данные.

    Переданные поля обновляются.
    Остальные остаются без изменений.
    """

    user = ensure_user(
        chat_id,
        max_user_id=user_id,
    )

    with engine.begin() as connection:
        existing = connection.execute(
            text("""
                SELECT
                    Email,
                    Phone
                FROM app.Contacts
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["id"],
            },
        ).mappings().first()

        if existing:
            new_email = (
                existing["Email"]
                if email is None
                else (email or None)
            )

            new_phone = (
                existing["Phone"]
                if phone is None
                else (phone or None)
            )

            connection.execute(
                text("""
                    UPDATE app.Contacts
                    SET
                        Email = :email,
                        Phone = :phone,
                        UpdatedAt = SYSUTCDATETIME()
                    WHERE UserId = :user_id
                """),
                {
                    "user_id": user["id"],
                    "email": new_email,
                    "phone": new_phone,
                },
            )

        else:
            connection.execute(
                text("""
                    INSERT INTO app.Contacts
                    (
                        UserId,
                        Email,
                        Phone
                    )
                    VALUES
                    (
                        :user_id,
                        :email,
                        :phone
                    )
                """),
                {
                    "user_id": user["id"],
                    "email": email or None,
                    "phone": phone or None,
                },
            )

    result = get_lead(chat_id)

    print(
        f"[storage] Лид {chat_id}: "
        f"email={result.get('email')!r} "
        f"phone={result.get('phone')!r}"
    )

    return result


def delete_lead_field(
    chat_id: int,
    field: str,
) -> dict | None:
    """
    field: email | phone

    Если оба поля пустые — запись контакта удаляется.
    """

    if field not in {
        "email",
        "phone",
    }:
        raise ValueError(
            "Можно удалить только 'email' или 'phone'"
        )

    user = _get_user_row(chat_id)

    if not user:
        return None

    column = {
        "email": "Email",
        "phone": "Phone",
    }[field]

    with engine.begin() as connection:
        connection.execute(
            text(f"""
                UPDATE app.Contacts
                SET
                    {column} = NULL,
                    UpdatedAt = SYSUTCDATETIME()
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["Id"],
            },
        )

        row = connection.execute(
            text("""
                SELECT
                    Email,
                    Phone
                FROM app.Contacts
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["Id"],
            },
        ).mappings().first()

        if not row:
            return None

        if (
            not row["Email"]
            and not row["Phone"]
        ):
            connection.execute(
                text("""
                    DELETE FROM app.Contacts
                    WHERE UserId = :user_id
                """),
                {
                    "user_id": user["Id"],
                },
            )

            return None

    return get_lead(chat_id)

def add_subscriber(
    chat_id: int,
    max_user_id: int | None = None,
) -> None:
    """
    Добавляет пользователя в подписчики.
    """

    user = ensure_user(
        chat_id,
        max_user_id=max_user_id,
    )

    with engine.begin() as connection:
        existing = connection.execute(
            text("""
                SELECT Id
                FROM app.Subscriptions
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["id"],
            },
        ).first()

        if existing:
            connection.execute(
                text("""
                    UPDATE app.Subscriptions
                    SET
                        Subscribed = 1,
                        UpdatedAt = SYSUTCDATETIME()
                    WHERE UserId = :user_id
                """),
                {
                    "user_id": user["id"],
                },
            )
        else:
            connection.execute(
                text("""
                    INSERT INTO app.Subscriptions
                    (
                        UserId,
                        Subscribed
                    )
                    VALUES
                    (
                        :user_id,
                        1
                    )
                """),
                {
                    "user_id": user["id"],
                },
            )

    print(
        f"[storage] Пользователь {chat_id} "
        f"подписан на рассылку"
    )


def load_subscribers() -> set:
    """
    Возвращает set из chat_id активных подписчиков.
    """

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT u.ChatId
                FROM app.Subscriptions s
                INNER JOIN app.Users u
                    ON u.Id = s.UserId
                WHERE s.Subscribed = 1
            """)
        ).all()

    return {
        row[0]
        for row in rows
    }


def remove_subscriber(chat_id: int) -> None:
    """
    Отключает пользователя от рассылки.
    """

    user = _get_user_row(chat_id)

    if not user:
        return

    with engine.begin() as connection:
        connection.execute(
            text("""
                UPDATE app.Subscriptions
                SET
                    Subscribed = 0,
                    UpdatedAt = SYSUTCDATETIME()
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["Id"],
            },
        )


def reset_user(
    chat_id: int,
    keep_role: bool = True,
) -> None:
    """
    Сбрасывает пользовательские данные.

    Удаляются:
        Contacts
        UserStates
        Subscriptions

    В Users:
        Consent = 0
        Onboarded = 0

    Сам пользователь и его роль сохраняются.

    Это удобно для /restart разработчика.
    """

    user = _get_user_row(chat_id)

    if not user:
        return

    with engine.begin() as connection:
        # Состояние диалога
        connection.execute(
            text("""
                DELETE FROM app.UserStates
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["Id"],
            },
        )

        # Контакты
        connection.execute(
            text("""
                DELETE FROM app.Contacts
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["Id"],
            },
        )

        # Подписка
        connection.execute(
            text("""
                DELETE FROM app.Subscriptions
                WHERE UserId = :user_id
            """),
            {
                "user_id": user["Id"],
            },
        )

        if keep_role:
            connection.execute(
                text("""
                    UPDATE app.Users
                    SET
                        Consent = 0,
                        Onboarded = 0,
                        UpdatedAt = SYSUTCDATETIME()
                    WHERE Id = :user_id
                """),
                {
                    "user_id": user["Id"],
                },
            )
        else:
            connection.execute(
                text("""
                    UPDATE app.Users
                    SET
                        Role = N'user',
                        Consent = 0,
                        Onboarded = 0,
                        UpdatedAt = SYSUTCDATETIME()
                    WHERE Id = :user_id
                """),
                {
                    "user_id": user["Id"],
                },
            )

    print(
        f"[storage] Полный сброс пользователя "
        f"{chat_id} выполнен"
    )