import pytest
from app import create_app, db
from app.models import User, PensionFund, Investment, Stock
import os as osalt


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

            # Создаем тестового пользователя и данные
            user = User(username='testuser')
            user.set_password('testpassword')
            db.session.add(user)
            db.session.commit()

            # Добавляем средства в пенсионный фонд
            db.session.add(PensionFund(user_id=user.id, amount=1000.00))
            db.session.commit()

            # Добавляем акции в базу данных
            stock1 = Stock(id=1, ticker='AAPL', name='Apple Inc.', current_price=150.00)
            stock2 = Stock(id=2, ticker='GOOG', name='Google', current_price=200.00)
            db.session.add_all([stock1, stock2])
            db.session.commit()

            # Авторизуем пользователя для тестов
            with client.session_transaction() as session:
                session['user_id'] = user.id
                session['username'] = user.username

            yield client

        import os
        if os.path.exists(db_path):
            os.remove(db_path)


def test_buy_stock_success(client):
    """Позитивный тест успешной покупки акций."""
    response = client.post('/buy_stock', data={
        'stock_id': 1,
        'quantity': '5'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Акции успешно куплены.' in response.data.decode('utf-8')

    # Проверяем, что баланс уменьшился
    user = User.query.filter_by(username='testuser').first()
    total_balance = sum(fund.amount for fund in user.pension_funds)
    assert total_balance == 250.00  # 1000 - (5 * 150)

    # Проверяем, что акции добавлены
    investment = Investment.query.filter_by(user_id=user.id, stock_id=1).first()
    assert investment.quantity == 5
    assert investment.invested_amount == 750.00


def test_buy_stock_insufficient_funds(client):
    """Негативный тест попытки купить акции при недостатке средств."""
    response = client.post('/buy_stock', data={
        'stock_id': 2,
        'quantity': '10'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Недостаточно средств для покупки акций.' in response.data.decode('utf-8')

    # Проверяем, что баланс не изменился
    user = User.query.filter_by(username='testuser').first()
    total_balance = sum(fund.amount for fund in user.pension_funds)
    assert total_balance == 1000.00


def test_sell_stock_success(client):
    """Позитивный тест успешной продажи акций."""
    # Добавляем акции в портфель перед тестом
    user = User.query.filter_by(username='testuser').first()
    db.session.add(Investment(user_id=user.id, stock_id=1, quantity=10, invested_amount=1500.00))
    db.session.commit()

    response = client.post('/sell_stock', data={
        'stock_id': 1,
        'quantity': '5'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Акции успешно проданы!' in response.json['message']

    # Проверяем, что баланс увеличился
    total_balance = sum(fund.amount for fund in user.pension_funds)
    assert total_balance == 1750.00  # 1000 + (5 * 150)

    # Проверяем, что количество акций уменьшилось
    investment = Investment.query.filter_by(user_id=user.id, stock_id=1).first()
    assert investment.quantity == 5
    assert investment.invested_amount == 750.00


def test_sell_stock_insufficient_quantity(client):
    """Негативный тест попытки продать больше акций, чем есть."""
    # Добавляем акции в портфель перед тестом
    user = User.query.filter_by(username='testuser').first()
    db.session.add(Investment(user_id=user.id, stock_id=2, quantity=2, invested_amount=400.00))
    db.session.commit()

    response = client.post('/sell_stock', data={
        'stock_id': 2,
        'quantity': '3'
    }, follow_redirects=True)

    assert response.status_code == 400
    assert 'Недостаточно акций для продажи.' in response.json['message']

    # Проверяем, что количество акций не изменилось
    investment = Investment.query.filter_by(user_id=user.id, stock_id=2).first()
    assert investment.quantity == 2


def test_buy_stock_not_found(client):
    """Негативный тест попытки купить несуществующую акцию."""
    response = client.post('/buy_stock', data={
        'stock_id': 999,
        'quantity': '1'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Акция не найдена.' in response.data.decode('utf-8')


def test_sell_stock_not_found(client):
    """Негативный тест попытки продать несуществующую акцию."""
    response = client.post('/sell_stock', data={
        'stock_id': 999,
        'quantity': '1'
    })

    assert response.status_code == 404
    assert 'Акция не найдена.' in response.json['message']
