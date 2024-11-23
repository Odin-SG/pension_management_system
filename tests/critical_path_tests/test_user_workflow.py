import pytest
from app import create_app, db
from app.models import User, PensionFund, Stock, Investment, InterestRate
from datetime import datetime


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()

            # Создание базовых данных
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin')
            db.session.add(admin_user)

            user = User(username='testuser', role='user')
            user.set_password('testpassword')
            db.session.add(user)

            # Коммитим пользователей, чтобы их ID стали доступны
            db.session.commit()

            # Используем сгенерированный ID пользователя для создания записи в пенсионном фонде
            pension_fund = PensionFund(user_id=user.id, amount=500.00, contribution_date=datetime.utcnow())
            db.session.add(pension_fund)

            # Добавляем акции
            stock1 = Stock(name='Apple', ticker='AAPL', current_price=150.0)
            stock2 = Stock(name='Google', ticker='GOOGL', current_price=2800.0)
            db.session.add(stock1)
            db.session.add(stock2)

            # Добавляем глобальную процентную ставку
            db.session.add(InterestRate(user_id=0, rate=5.0))

            db.session.commit()

            yield client


def test_user_workflow(client):
    """Полный сценарий работы пользователя с приложением."""

    # 1. Регистрация нового пользователя
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'newpassword',
        'confirm_password': 'newpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Регистрация прошла успешно!' in response.data.decode('utf-8')

    # 2. Вход в систему
    response = client.post('/login', data={
        'username': 'newuser',
        'password': 'newpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Добро пожаловать, newuser!' in response.data.decode('utf-8')

    # 3. Проверка пенсионного баланса
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert 'Общая сумма накоплений:' in response.data.decode('utf-8')
    assert '0.00' in response.data.decode('utf-8')

    # 4. Пополнение пенсионного баланса
    response = client.post('/contribute', data={
        'amount': '60000.00'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Вклад успешно внесен!' in response.data.decode('utf-8')

    # Проверяем, что баланс обновился
    response = client.get('/dashboard')
    assert '60 000.00' in response.data.decode('utf-8')

    # 5. Покупка акций
    response = client.post('/buy_stock', data={
        'stock_id': 1,  # Apple (AAPL)
        'quantity': '2'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Акции успешно куплены.' in response.data.decode('utf-8')

    # Проверяем инвестиционный портфель
    response = client.get('/investments')
    assert response.status_code == 200
    assert 'Apple' in response.data.decode('utf-8')
    assert '2.0 шт. акций' in response.data.decode('utf-8')

    # Проверяем, что баланс уменьшился
    response = client.get('/dashboard')
    assert '59 700.00' in response.data.decode('utf-8')

    # 6. Продажа акций
    response = client.post('/sell_stock', data={
        'stock_id': 1,  # Apple (AAPL)
        'quantity': '1'
    })
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['message'] == 'Акции успешно проданы!'

    # Проверяем инвестиционный портфель
    response = client.get('/investments')
    assert response.status_code == 200
    assert '1.0 шт. акций' in response.data.decode('utf-8')

    # Проверяем, что баланс увеличился
    response = client.get('/dashboard')
    assert '59 850.00' in response.data.decode('utf-8')

    # 7. Выход из системы
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert 'Вы успешно вышли из системы.' in response.data.decode('utf-8')

    # 8. Попытка зайти в защищенные разделы без авторизации
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert 'Пожалуйста, войдите в систему, чтобы получить доступ к личному кабинету' in response.data.decode('utf-8')

    response = client.get('/investments', follow_redirects=True)
    assert response.status_code == 200
    assert 'Пожалуйста, войдите в систему, чтобы получить доступ к личному кабинету' in response.data.decode('utf-8')
