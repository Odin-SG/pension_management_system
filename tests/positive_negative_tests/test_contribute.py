import pytest
from app import create_app, db
from app.models import User, InterestRate
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

            # Создаем тестового пользователя
            user = User(username='testuser')
            user.set_password('testpassword')
            db.session.add(InterestRate(user_id=0, rate=5.0))
            db.session.add(user)
            db.session.commit()

            # Авторизуем пользователя для тестов
            with client.session_transaction() as session:
                session['user_id'] = user.id
                session['username'] = user.username

            yield client

        import os
        if os.path.exists(db_path):
            os.remove(db_path)


def test_contribute_success(client):
    """Позитивный тест успешного внесения пенсионных накоплений."""
    response = client.post('/contribute', data={
        'amount': '100.50'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Вклад успешно внесен!' in response.data.decode('utf-8')

    # Проверяем, что вклад добавлен в базу данных
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 100.50


def test_contribute_negative_amount(client):
    """Негативный тест внесения отрицательной суммы."""
    response = client.post('/contribute', data={
        'amount': '-50.00'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Сумма вклада должна быть положительной.' in response.data.decode('utf-8')

    # Проверяем, что вклад не добавлен в базу данных
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 0.0


def test_contribute_empty_amount(client):
    """Негативный тест внесения пустого значения."""
    response = client.post('/contribute', data={
        'amount': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Пожалуйста, укажите сумму вклада.' in response.data.decode('utf-8')

    # Проверяем, что вклад не добавлен в базу данных
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 0.0


def test_contribute_large_amount(client):
    """Позитивный тест внесения крупной суммы."""
    response = client.post('/contribute', data={
        'amount': '1000000.00'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Вклад успешно внесен!' in response.data.decode('utf-8')

    # Проверяем, что вклад добавлен в базу данных
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 1000000.00


def test_contribute_invalid_format(client):
    """Негативный тест внесения некорректного формата суммы."""
    response = client.post('/contribute', data={
        'amount': 'abc123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Пожалуйста, введите корректную сумму вклада.' in response.data.decode('utf-8')

    # Проверяем, что вклад не добавлен в базу данных
    user = User.query.filter_by(username='testuser').first()
    total_amount = sum(fund.amount for fund in user.pension_funds)
    assert total_amount == 0.0
