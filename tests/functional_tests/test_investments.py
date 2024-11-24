import pytest
import os as osalt
from flask import session
from app import create_app, db
from app.models import User, Stock, Investment, PensionFund, StockPriceHistory, InterestRate
from datetime import datetime


@pytest.fixture
def client():
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

            # Добавляем тестовую акцию
            stock = Stock(name='Test Stock', ticker='TST', current_price=100.0)
            db.session.add(stock)

            # Добавляем стартовые средства в пенсионный фонд
            pension_fund = PensionFund(user_id=1, amount=1000.0, contribution_date=datetime.utcnow())
            db.session.add(pension_fund)

            # Добавляем глобальную процентную ставку
            db.session.add(InterestRate(user_id=0, rate=5.0))

            db.session.commit()
            yield client

        import os
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest.fixture
def login_user(client):
    """Фикстура для авторизации пользователя перед тестами."""
    client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})


def test_investments_page(client, login_user):
    """Тест страницы инвестиций."""
    response = client.get('/investments')
    assert response.status_code == 200
    assert '<h1>Инвестиции</h1>' in response.data.decode('utf-8')
    assert 'Test Stock' in response.data.decode('utf-8')


def test_buy_stock_success(client, login_user):
    """Тест успешной покупки акций."""
    response = client.post('/buy_stock', data={'stock_id': 1, 'quantity': 5}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Акции успешно куплены.' in response.data.decode('utf-8')

    # Проверяем, что акции добавлены в портфель
    investment = Investment.query.filter_by(user_id=1, stock_id=1).first()
    assert investment is not None
    assert investment.quantity == 5
    assert investment.invested_amount == 500.0  # 5 * 100.0

    # Проверяем, что средства списаны из пенсионного фонда
    funds = PensionFund.query.filter_by(user_id=1).all()
    total_balance = sum(fund.amount for fund in funds)
    assert total_balance == 500.0  # 1000 - 500


def test_buy_stock_insufficient_funds(client, login_user):
    """Тест покупки акций при недостатке средств."""
    response = client.post('/buy_stock', data={'stock_id': 1, 'quantity': 20}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Недостаточно средств для покупки акций.' in response.data.decode('utf-8')

    # Проверяем, что инвестиция не создана
    investment = Investment.query.filter_by(user_id=1, stock_id=1).first()
    assert investment is None


def test_sell_stock_success(client, login_user):
    """Тест успешной продажи акций."""
    # Покупаем акции для теста продажи
    client.post('/buy_stock', data={'stock_id': 1, 'quantity': 5}, follow_redirects=True)

    # Продаем часть акций
    response = client.post('/sell_stock', data={'stock_id': 1, 'quantity': 2}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Акции успешно проданы!' in response.json['message']

    # Проверяем, что инвестиция обновлена
    investment = Investment.query.filter_by(user_id=1, stock_id=1).first()
    assert investment is not None
    assert investment.quantity == 3
    assert investment.invested_amount == 300.0  # 3 * 100.0

    # Проверяем, что средства добавлены в пенсионный фонд
    funds = PensionFund.query.filter_by(user_id=1).all()
    total_balance = sum(fund.amount for fund in funds)
    assert total_balance == 700.0  # 1000 - 500 + 200


def test_sell_stock_insufficient_quantity(client, login_user):
    """Тест продажи большего количества акций, чем имеется."""
    # Покупаем акции для теста продажи
    client.post('/buy_stock', data={'stock_id': 1, 'quantity': 5}, follow_redirects=True)

    # Пробуем продать больше, чем есть
    response = client.post('/sell_stock', data={'stock_id': 1, 'quantity': 10}, follow_redirects=False)
    assert response.status_code == 400
    assert 'Недостаточно акций для продажи.' in response.json['message']


def test_get_prices(client):
    """Тест получения текущих цен на акции."""
    response = client.get('/get_prices')
    assert response.status_code == 200
    prices = response.json
    assert len(prices) == 1
    assert prices[0]['ticker'] == 'TST'
    assert prices[0]['price'] == 100.0


def test_stock_prices_history(client):
    """Тест получения истории цен на акции."""
    # Добавляем исторические данные цен
    history_entry = StockPriceHistory(stock_id=1, price=100.0, timestamp=datetime.utcnow())
    db.session.add(history_entry)
    db.session.commit()

    response = client.get('/stock_prices/1')
    assert response.status_code == 200
    history = response.json
    assert len(history) == 1
    assert history[0]['price'] == 100.0
