import requests
import json
import random

BASE_URL = "http://127.0.0.1:8000"

UNIQUE_ID = random.randint(1, 10000)
TEST_USERNAME = f"testuser_{UNIQUE_ID}"
TEST_EMAIL = f"test_{UNIQUE_ID}@test.com"

def test_register():
    data = {
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "password": "123"
    }
    response = requests.post(f"{BASE_URL}/register", json=data)

    if response.status_code == 200:
        print("✅ TC-01 Регистрация: УСПЕШНО")
        return True
    else:
        print(f"❌ TC-01 Регистрация: ОШИБКА ({response.status_code}) - {response.text}")
        return False


def test_duplicate_register():
    data = {
        "username": TEST_USERNAME,
        "email": f"new_{UNIQUE_ID}@test.com",
        "password": "123"
    }
    response = requests.post(f"{BASE_URL}/register", json=data)

    if response.status_code == 400:
        print("✅ TC-02 Дубликат регистрации: УСПЕШНО (ошибка 400)")
        return True
    else:
        print(f"❌ TC-02 Дубликат регистрации: ОШИБКА ({response.status_code})")
        return False


def test_login():
    data = {
        "username": TEST_USERNAME,
        "password": "123"
    }
    response = requests.post(f"{BASE_URL}/login", data=data)

    if response.status_code == 200:
        token = response.json().get("access_token")
        user_id = response.json().get("user_id")
        print("✅ TC-03 Логин: УСПЕШНО")
        return token, user_id
    else:
        print(f"❌ TC-03 Логин: ОШИБКА ({response.status_code})")
        return None, None


def test_invalid_login():
    data = {
        "username": TEST_USERNAME,
        "password": "wrongpassword"
    }
    response = requests.post(f"{BASE_URL}/login", data=data)

    if response.status_code == 401:
        print("✅ TC-04 Неверный логин: УСПЕШНО (ошибка 401)")
        return True
    else:
        print(f"❌ TC-04 Неверный логин: ОШИБКА ({response.status_code})")
        return False


def test_create_product(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": f"Тестовый товар_{UNIQUE_ID}",
        "price": 1000,
        "stock": 10
    }
    response = requests.post(f"{BASE_URL}/products", json=data, headers=headers)

    if response.status_code == 200:
        product_id = response.json().get("id")
        print(f"✅ TC-05 Создание товара: УСПЕШНО (ID: {product_id})")
        return product_id
    else:
        print(f"❌ TC-05 Создание товара: ОШИБКА ({response.status_code}) - {response.text}")
        return None


def test_add_to_cart(token, product_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/cart/add/{product_id}?quantity=2", headers=headers)

    if response.status_code == 200:
        print("✅ TC-06 Добавление в корзину: УСПЕШНО")
        return True
    else:
        print(f"❌ TC-06 Добавление в корзину: ОШИБКА ({response.status_code}) - {response.text}")
        return False


def test_get_cart(token, username):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/cart/{username}", headers=headers)

    if response.status_code == 200:
        items = response.json().get("items", [])
        print(f"✅ TC-07 Просмотр корзины: УСПЕШНО (товаров: {len(items)})")
        return True
    else:
        print(f"❌ TC-07 Просмотр корзины: ОШИБКА ({response.status_code})")
        return False


def test_create_order(token, product_id):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {
        "delivery_address": "г. Москва, ул. Тестовая, д.1",
        "items": [{"product_id": product_id, "quantity": 1}]
    }
    response = requests.post(f"{BASE_URL}/orders", json=data, headers=headers)

    if response.status_code == 200:
        order_id = response.json().get("id")
        print(f"✅ TC-08 Создание заказа: УСПЕШНО (ID: {order_id})")
        return order_id
    else:
        print(f"❌ TC-08 Создание заказа: ОШИБКА ({response.status_code}) - {response.text}")
        return None


def test_pay_order(token, order_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/orders/id/{order_id}/pay", headers=headers)

    if response.status_code == 200:
        print("✅ TC-09 Оплата заказа: УСПЕШНО")
        return True
    else:
        print(f"❌ TC-09 Оплата заказа: ОШИБКА ({response.status_code}) - {response.text}")
        return False


def run_all_tests():
    print("=" * 60)
    print("ЗАПУСК АВТОМАТИЗИРОВАННОГО ТЕСТИРОВАНИЯ")
    print("=" * 60)
    print()

    reg_ok = test_register()
    test_duplicate_register()

    token, user_id = test_login()
    test_invalid_login()

    if not token:
        print("\n❌ Невозможно продолжить тестирование: нет токена")
        return

    product_id = test_create_product(token)

    if not product_id:
        print("\n❌ Невозможно продолжить тестирование: нет товара")
        return

    test_add_to_cart(token, product_id)

    test_get_cart(token, TEST_USERNAME)

    order_id = test_create_order(token, product_id)

    if order_id:
        test_pay_order(token, order_id)

    print()
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()