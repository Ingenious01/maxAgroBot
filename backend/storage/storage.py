import json

from sqlalchemy import text

from backend.storage.database import engine


def _get_user_row(chat_id: int):
    """Пользователь из app.Users по ChatId."""
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
            {"chat_id": chat_id},
        ).mappings().first()


def ensure_user(
    chat_id: int,
    max_user_id: int | None = None,
) -> dict:
    """
    Находит пользователя или создаёт его.

    max_user_id — user_id в MAX.
    Если не передан, временно пишется chat_id; при следующем вызове с
    реальным max_user_id значение обновится.
    """
    row = _get_user_row(chat_id)

    if row:
        if max_user_id is not None and row["MaxUserId"] != max_user_id:
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

    real_max_user_id = max_user_id if max_user_id is not None else chat_id

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


def get_user(
    chat_id: int | None = None,
    user_id: int | None = None,
) -> dict:
    """
    user_id = MaxUserId (miniapp).
    chat_id = ChatId (бот).
    """
    with engine.connect() as connection:
        if user_id is not None:
            row = connection.execute(
                text("""
                    SELECT
                        Id, MaxUserId, ChatId, Role, Consent, Onboarded
                    FROM app.Users
                    WHERE MaxUserId = :max_user_id
                """),
                {"max_user_id": user_id},
            ).mappings().first()
            if row:
                return {
                    "id": row["Id"],
                    "max_user_id": row["MaxUserId"],
                    "chat_id": row["ChatId"],
                    "role": row["Role"],
                    "consent": bool(row["Consent"]),
                    "onboarded": bool(row["Onboarded"]),
                }

        if chat_id is not None:
            row = _get_user_row(chat_id)
            if row:
                return {
                    "id": row["Id"],
                    "max_user_id": row["MaxUserId"],
                    "chat_id": row["ChatId"],
                    "role": row["Role"],
                    "consent": bool(row["Consent"]),
                    "onboarded": bool(row["Onboarded"]),
                }

    return {
        "consent": False,
        "onboarded": False,
        "max_user_id": user_id,
        "chat_id": chat_id,
    }


def update_user(
    chat_id: int,
    max_user_id: int | None = None,
    user_id: int | None = None,  # алиас
    **fields,
) -> dict:
    uid = max_user_id if max_user_id is not None else user_id
    user = ensure_user(chat_id, max_user_id=uid)
    # ... дальше UPDATE Consent/Onboarded как в итоговом storage

    sets = []
    params: dict = {"user_id": user["id"]}

    if "consent" in fields:
        sets.append("Consent = :consent")
        params["consent"] = 1 if fields["consent"] else 0

    if "onboarded" in fields:
        sets.append("Onboarded = :onboarded")
        params["onboarded"] = 1 if fields["onboarded"] else 0

    if "role" in fields and fields["role"] is not None:
        sets.append("Role = :role")
        params["role"] = fields["role"]

    if user_id is not None:
        sets.append("MaxUserId = :max_user_id")
        params["max_user_id"] = user_id

    if sets:
        sets.append("UpdatedAt = SYSUTCDATETIME()")
        sql = f"""
            UPDATE app.Users
            SET {", ".join(sets)}
            WHERE Id = :user_id
        """
        with engine.begin() as connection:
            connection.execute(text(sql), params)

    return get_user(chat_id=chat_id, user_id=user_id)


def set_state(
    chat_id: int,
    state: str | None,
    pending: dict | None = None,
) -> None:
    user = ensure_user(chat_id)

    if state is None:
        with engine.begin() as connection:
            connection.execute(
                text("""
                    DELETE FROM app.UserStates
                    WHERE UserId = :user_id
                """),
                {"user_id": user["id"]},
            )
        return

    pending_json = None
    if pending is not None:
        pending_json = json.dumps(pending, ensure_ascii=False)

    with engine.begin() as connection:
        existing = connection.execute(
            text("""
                SELECT Id
                FROM app.UserStates
                WHERE UserId = :user_id
            """),
            {"user_id": user["id"]},
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
                    (UserId, State, PendingData)
                    VALUES
                    (:user_id, :state, :pending_data)
                """),
                {
                    "user_id": user["id"],
                    "state": state,
                    "pending_data": pending_json,
                },
            )


def get_state(chat_id: int) -> str | None:
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
            {"user_id": user["Id"]},
        ).first()

    if not row:
        return None
    return row[0]


def get_pending(chat_id: int) -> dict | None:
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
            {"user_id": user["Id"]},
        ).first()

    if not row or not row[0]:
        return None

    try:
        return json.loads(row[0])
    except (TypeError, json.JSONDecodeError):
        return None


def get_lead(chat_id: int) -> dict | None:
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
                INNER JOIN app.Users u ON u.Id = c.UserId
                WHERE c.UserId = :user_id
            """),
            {"user_id": user["Id"]},
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
    user = ensure_user(chat_id, max_user_id=user_id)

    with engine.begin() as connection:
        existing = connection.execute(
            text("""
                SELECT Email, Phone
                FROM app.Contacts
                WHERE UserId = :user_id
            """),
            {"user_id": user["id"]},
        ).mappings().first()

        if existing:
            new_email = existing["Email"] if email is None else (email or None)
            new_phone = existing["Phone"] if phone is None else (phone or None)

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
                    INSERT INTO app.Contacts (UserId, Email, Phone)
                    VALUES (:user_id, :email, :phone)
                """),
                {
                    "user_id": user["id"],
                    "email": email or None,
                    "phone": phone or None,
                },
            )

    result = get_lead(chat_id) or {
        "email": email,
        "phone": phone,
        "user_id": user_id,
    }
    print(
        f"[storage] Лид {chat_id}: "
        f"email={result.get('email')!r} phone={result.get('phone')!r}"
    )
    return result


def delete_lead_field(chat_id: int, field: str) -> dict | None:
    if field not in {"email", "phone"}:
        raise ValueError("Можно удалить только 'email' или 'phone'")

    user = _get_user_row(chat_id)
    if not user:
        return None

    column = {"email": "Email", "phone": "Phone"}[field]

    with engine.begin() as connection:
        connection.execute(
            text(f"""
                UPDATE app.Contacts
                SET
                    {column} = NULL,
                    UpdatedAt = SYSUTCDATETIME()
                WHERE UserId = :user_id
            """),
            {"user_id": user["Id"]},
        )

        row = connection.execute(
            text("""
                SELECT Email, Phone
                FROM app.Contacts
                WHERE UserId = :user_id
            """),
            {"user_id": user["Id"]},
        ).mappings().first()

        if not row:
            return None

        if not row["Email"] and not row["Phone"]:
            connection.execute(
                text("""
                    DELETE FROM app.Contacts
                    WHERE UserId = :user_id
                """),
                {"user_id": user["Id"]},
            )
            return None

    return get_lead(chat_id)


def add_subscriber(
    chat_id: int,
    max_user_id: int | None = None,
) -> None:
    user = ensure_user(chat_id, max_user_id=max_user_id)

    with engine.begin() as connection:
        existing = connection.execute(
            text("""
                SELECT Id
                FROM app.Subscriptions
                WHERE UserId = :user_id
            """),
            {"user_id": user["id"]},
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
                {"user_id": user["id"]},
            )
        else:
            connection.execute(
                text("""
                    INSERT INTO app.Subscriptions (UserId, Subscribed)
                    VALUES (:user_id, 1)
                """),
                {"user_id": user["id"]},
            )

    print(f"[storage] Пользователь {chat_id} подписан на рассылку")


def load_subscribers() -> set:
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT u.ChatId
                FROM app.Subscriptions s
                INNER JOIN app.Users u ON u.Id = s.UserId
                WHERE s.Subscribed = 1
            """)
        ).all()

    return {row[0] for row in rows}


def remove_subscriber(chat_id: int) -> None:
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
            {"user_id": user["Id"]},
        )


def reset_user(chat_id: int, keep_role: bool = True) -> None:
    user = _get_user_row(chat_id)
    if not user:
        return

    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM app.UserStates WHERE UserId = :user_id"),
            {"user_id": user["Id"]},
        )
        connection.execute(
            text("DELETE FROM app.Contacts WHERE UserId = :user_id"),
            {"user_id": user["Id"]},
        )
        connection.execute(
            text("DELETE FROM app.Subscriptions WHERE UserId = :user_id"),
            {"user_id": user["Id"]},
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
                {"user_id": user["Id"]},
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
                {"user_id": user["Id"]},
            )

    print(f"[storage] Полный сброс пользователя {chat_id} выполнен")