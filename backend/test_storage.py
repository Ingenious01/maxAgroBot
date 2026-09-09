from backend.storage.storage import (
    ensure_user,
    get_user,
    update_user,
    set_state,
    get_state,
    get_pending,
    get_lead,
    upsert_lead,
    delete_lead_field,
    add_subscriber,
    load_subscribers,
    reset_user,
)


TEST_CHAT_ID = 999999991
TEST_MAX_USER_ID = 999999992


def main():
    print("=== 1. Создание пользователя ===")

    user = ensure_user(
        TEST_CHAT_ID,
        max_user_id=TEST_MAX_USER_ID,
    )

    print(user)

    print("\n=== 2. Чтение пользователя ===")

    user = get_user(TEST_CHAT_ID)

    print(user)

    print("\n=== 3. Обновление пользователя ===")

    user = update_user(
        TEST_CHAT_ID,
        max_user_id=TEST_MAX_USER_ID,
        consent=True,
        onboarded=True,
    )

    print(user)

    print("\n=== 4. Состояние ===")

    set_state(
        TEST_CHAT_ID,
        "wait_confirm",
        pending={
            "email": "test@example.com",
            "user_id": TEST_MAX_USER_ID,
        },
    )

    print("state:", get_state(TEST_CHAT_ID))
    print("pending:", get_pending(TEST_CHAT_ID))

    print("\n=== 5. Контакт ===")

    lead = upsert_lead(
        TEST_CHAT_ID,
        user_id=TEST_MAX_USER_ID,
        email="test@example.com",
    )

    print(lead)

    print("Чтение:", get_lead(TEST_CHAT_ID))

    print("\n=== 6. Изменение контакта ===")

    lead = upsert_lead(
        TEST_CHAT_ID,
        phone="+79991234567",
    )

    print(lead)

    print("\n=== 7. Подписка ===")

    add_subscriber(
        TEST_CHAT_ID,
        max_user_id=TEST_MAX_USER_ID,
    )

    subscribers = load_subscribers()

    print("Подписчики:", subscribers)

    print("\n=== 8. Сброс пользователя ===")

    reset_user(TEST_CHAT_ID)

    print("После сброса:")
    print("user:", get_user(TEST_CHAT_ID))
    print("lead:", get_lead(TEST_CHAT_ID))
    print("state:", get_state(TEST_CHAT_ID))
    print("pending:", get_pending(TEST_CHAT_ID))
    print("subscribers:", load_subscribers())

    print("\n=== ТЕСТ ЗАВЕРШЁН ===")


if __name__ == "__main__":
    main()