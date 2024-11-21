import pytest
import os
from flask import url_for, session
from app import create_app, db
from app.models import User, PensionFund, InterestRate


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True

    # Определяем абсолютный путь до файла базы данных
    db_path = os.path.join(os.path.dirname(__file__), '../test.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # Используем полный путь

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()  # Удаляем все таблицы, если они существуют
            db.create_all()  # Создаем заново
            # Добавляем тестовые данные
            user = User(username='testuser')
            user.set_password('testpassword')
            db.session.add(user)
            db.session.add(InterestRate(user_id=0, rate=5.0))
            db.session.commit()
            yield client

        # Удаляем файл базы данных после тестов
        if os.path.exists(db_path):
            os.remove(db_path)

@pytest.fixture
def login_user(client):
    """Фикстура для авторизации пользователя перед тестами."""
    client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})


def test_dashboard_data(client, login_user):
    """Тест получения данных на дашборде."""
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert '<title>Личный Кабинет</title>' in response.data.decode('utf-8')


def test_contribute_success(client, login_user):
    """Тест успешного внесения средств."""
    response = client.post('/contribute', data={'amount': '100.50'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Вклад успешно внесен!' in response.data.decode('utf-8')

    # Проверяем, что вклад добавлен в базу данных
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 100.50


def test_contribute_negative_amount(client, login_user):
    """Тест внесения отрицательной суммы."""
    response = client.post('/contribute', data={'amount': '-50.00'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Сумма вклада должна быть положительной.' in response.data.decode('utf-8')


def test_withdraw_success(client, login_user):
    """Тест успешного снятия средств."""
    # Сначала внесем средства
    client.post('/contribute', data={'amount': '200.00'}, follow_redirects=True)

    # Затем снимаем часть средств
    response = client.post('/withdraw', data={'amount': '50.00'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Снятие средств успешно выполнено!' in response.data.decode('utf-8')

    # Проверяем, что сумма в пенсионном фонде уменьшилась
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 150.00


def test_withdraw_insufficient_funds(client, login_user):
    """Тест попытки снять больше средств, чем есть."""
    # Сначала внесем средства
    client.post('/contribute', data={'amount': '100.00'}, follow_redirects=True)

    # Попытаемся снять больше, чем есть
    response = client.post('/withdraw', data={'amount': '150.00'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Недостаточно средств для снятия.' in response.data.decode('utf-8')


def test_withdraw_negative_amount(client, login_user):
    """Тест попытки снять отрицательную сумму."""
    response = client.post('/withdraw', data={'amount': '-100.00'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Сумма снятия должна быть положительной.' in response.data.decode('utf-8')
