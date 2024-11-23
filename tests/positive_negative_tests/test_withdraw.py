import pytest
from app import create_app, db
from app.models import User, PensionFund, InterestRate
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

            # Создаем тестового пользователя и сохраняем его в базе данных
            user = User(username='testuser')
            user.set_password('testpassword')
            db.session.add(user)
            db.session.add(InterestRate(user_id=0, rate=5.0))
            db.session.commit()
            db.session.add(PensionFund(user_id=user.id, amount=500.00))  # Используем реальный user.id
            db.session.commit()

            # Авторизуем пользователя для тестов
            with client.session_transaction() as session:
                session['user_id'] = user.id
                session['username'] = user.username

            yield client

        import os
        if os.path.exists(db_path):
            os.remove(db_path)

def test_withdraw_success(client):
    """Позитивный тест успешного снятия средств."""
    response = client.post('/withdraw', data={
        'amount': '200.00'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Снятие средств успешно выполнено!' in response.data.decode('utf-8')

    # Проверяем, что сумма в пенсионном фонде уменьшилась
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 300.00


def test_withdraw_insufficient_funds(client):
    """Негативный тест попытки снять больше средств, чем есть."""
    response = client.post('/withdraw', data={
        'amount': '600.00'  # Больше, чем текущий баланс
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Недостаточно средств для снятия.' in response.data.decode('utf-8')

    # Проверяем, что сумма в пенсионном фонде осталась прежней
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 500.00


def test_withdraw_negative_amount(client):
    """Негативный тест попытки снять отрицательную сумму."""
    response = client.post('/withdraw', data={
        'amount': '-50.00'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Сумма снятия должна быть положительной.' in response.data.decode('utf-8')

    # Проверяем, что сумма в пенсионном фонде осталась прежней
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 500.00


def test_withdraw_empty_amount(client):
    """Негативный тест попытки снять пустую сумму."""
    response = client.post('/withdraw', data={
        'amount': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Пожалуйста, введите корректную сумму для снятия.' in response.data.decode('utf-8')

    # Проверяем, что сумма в пенсионном фонде осталась прежней
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 500.00


def test_withdraw_invalid_format(client):
    """Негативный тест попытки снять сумму некорректного формата."""
    response = client.post('/withdraw', data={
        'amount': 'abc123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Пожалуйста, введите корректную сумму для снятия.' in response.data.decode('utf-8')

    # Проверяем, что сумма в пенсионном фонде осталась прежней
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 500.00
