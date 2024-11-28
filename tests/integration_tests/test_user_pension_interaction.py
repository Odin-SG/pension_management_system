import pytest
from app import create_app, db
from app.models import User, PensionFund, Investment, Stock, InterestRate
from datetime import datetime, timedelta
import os as osalt


@pytest.fixture
def client():
    """Фикстура для тестового клиента Flask с тестовой базой данных."""
    app = create_app()
    app.config['TESTING'] = True
    db_path = osalt.path.join(osalt.path.dirname(__file__), '../test.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()

            # Создаем тестового пользователя
            user = User(username='testuser')
            user.set_password('testpassword')
            db.session.add(user)
            db.session.commit()

            # Добавляем пенсионный фонд
            db.session.add(PensionFund(user_id=user.id, amount=1000.00))
            db.session.add(InterestRate(user_id=0, rate=5.0))
            db.session.commit()

            # Добавляем акции
            stock1 = Stock(id=1, ticker='AAPL', name='Apple Inc.', current_price=150.00)
            stock2 = Stock(id=2, ticker='GOOG', name='Google', current_price=200.00)
            db.session.add_all([stock1, stock2])
            db.session.commit()

            # Авторизуем пользователя
            with client.session_transaction() as session:
                session['user_id'] = user.id
                session['username'] = user.username

            yield client

        if osalt.path.exists(db_path):
            osalt.remove(db_path)


def test_user_dashboard(client):
    """Тест личного кабинета пользователя."""
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert 'Личный Кабинет' in response.data.decode('utf-8')
    assert '1 000.00' in response.data.decode('utf-8')  # Проверяем отображение баланса


def test_user_contribute(client):
    """Тест внесения средств в пенсионный фонд."""
    response = client.post('/contribute', data={'amount': '500.00'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Вклад успешно внесен!' in response.data.decode('utf-8')

    # Проверяем, что баланс увеличился
    user = User.query.filter_by(username='testuser').first()
    total_balance = sum(fund.amount for fund in user.pension_funds)
    assert total_balance == 1500.00


def test_user_withdraw_success(client):
    """Тест успешного снятия средств из пенсионного фонда."""
    response = client.post('/withdraw', data={'amount': '300.00'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Снятие средств успешно выполнено!' in response.data.decode('utf-8')

    # Проверяем, что баланс уменьшился
    user = User.query.filter_by(username='testuser').first()
    total_balance = sum(fund.amount for fund in user.pension_funds)
    assert total_balance == 700.00


def test_user_withdraw_insufficient_funds(client):
    """Тест попытки снять больше средств, чем доступно."""
    response = client.post('/withdraw', data={'amount': '2000.00'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Недостаточно средств для снятия.' in response.data.decode('utf-8')

    # Баланс не должен измениться
    user = User.query.filter_by(username='testuser').first()
    total_balance = sum(fund.amount for fund in user.pension_funds)
    assert total_balance == 1000.00


def test_user_buy_stock(client):
    """Тест покупки акций пользователем."""
    response = client.post('/buy_stock', data={'stock_id': 1, 'quantity': '5'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Акции успешно куплены.' in response.data.decode('utf-8')

    # Проверяем баланс
    user = User.query.filter_by(username='testuser').first()
    total_balance = sum(fund.amount for fund in user.pension_funds)
    assert total_balance == 250.00  # 1000 - (5 * 150)

    # Проверяем инвестиции
    investment = Investment.query.filter_by(user_id=user.id, stock_id=1).first()
    assert investment.quantity == 5
    assert investment.invested_amount == 750.00


def test_user_sell_stock_success(client):
    """Тест успешной продажи акций."""
    # Добавляем акции в портфель
    user = User.query.filter_by(username='testuser').first()
    db.session.add(Investment(user_id=user.id, stock_id=1, quantity=10, invested_amount=1500.00))
    db.session.commit()

    response = client.post('/sell_stock', data={'stock_id': 1, 'quantity': '5'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Акции успешно проданы!' in response.json['message']

    # Проверяем баланс
    total_balance = sum(fund.amount for fund in user.pension_funds)
    assert total_balance == 1750.00  # 1000 + (5 * 150)

    # Проверяем инвестиции
    investment = Investment.query.filter_by(user_id=user.id, stock_id=1).first()
    assert investment.quantity == 5
    assert investment.invested_amount == 750.00


def test_user_sell_stock_insufficient_quantity(client):
    """Тест попытки продать больше акций, чем есть."""
    # Добавляем акции в портфель
    user = User.query.filter_by(username='testuser').first()
    db.session.add(Investment(user_id=user.id, stock_id=2, quantity=2, invested_amount=400.00))
    db.session.commit()

    response = client.post('/sell_stock', data={'stock_id': 2, 'quantity': '3'}, follow_redirects=True)
    assert response.status_code == 400
    assert 'Недостаточно акций для продажи.' in response.json['message']

    # Проверяем, что количество акций не изменилось
    investment = Investment.query.filter_by(user_id=user.id, stock_id=2).first()
    assert investment.quantity == 2