import pytest
from app import create_app, db
from app.models import User, InterestRate, PensionFund
from datetime import datetime
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

            # Создаем тестового менеджера
            manager = User(username='testmanager', role='manager')
            manager.set_password('testpassword')
            db.session.add(manager)

            # Создаем тестового пользователя
            user = User(username='testuser', role='user')
            user.set_password('userpassword')
            db.session.add(user)

            # Добавляем глобальную процентную ставку
            db.session.add(InterestRate(user_id=0, rate=5.0))
            db.session.commit()

            # Авторизуем менеджера
            with client.session_transaction() as session:
                session['user_id'] = manager.id
                session['username'] = manager.username
                session['role'] = manager.role

            yield client

        if osalt.path.exists(db_path):
            osalt.remove(db_path)


def test_update_global_interest_rate(client):
    """Тест успешного изменения глобальной процентной ставки менеджером."""
    response = client.post('/manager_panel', data={'interest_rate': '6.5'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Процентная ставка успешно обновлена.' in response.data.decode('utf-8')

    # Проверяем, что глобальная процентная ставка изменилась
    global_rate = InterestRate.query.filter_by(user_id=0).first()
    assert global_rate.rate == 6.5


def test_update_user_interest_rate(client):
    """Тест успешного изменения процентной ставки для конкретного пользователя менеджером."""
    # Получаем ID пользователя
    user = User.query.filter_by(username='testuser').first()
    response = client.post('/manager_panel', data={
        'user_id': user.id,
        'interest_rate': '4.2'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Процентная ставка успешно обновлена.' in response.data.decode('utf-8')

    # Проверяем, что пользовательская процентная ставка изменилась
    user_rate = InterestRate.query.filter_by(user_id=user.id).first()
    assert user_rate.rate == 4.2


def test_update_interest_rate_invalid_value(client):
    """Тест попытки установить некорректное значение процентной ставки."""
    response = client.post('/manager_panel', data={'interest_rate': '-3.0'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'Процентная ставка должна быть положительной.' in response.data.decode('utf-8')

    # Проверяем, что глобальная процентная ставка не изменилась
    global_rate = InterestRate.query.filter_by(user_id=0).first()
    assert global_rate.rate == 5.0


def test_update_interest_rate_user_not_found(client):
    """Тест попытки установить процентную ставку для несуществующего пользователя."""
    response = client.post('/manager_panel', data={
        'user_id': 999,  # Несуществующий ID
        'interest_rate': '3.5'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Пользователь не найден.' in response.data.decode('utf-8')

    # Убедимся, что для несуществующего пользователя процентная ставка не добавилась
    user_rate = InterestRate.query.filter_by(user_id=999).first()
    assert user_rate is None


def test_get_current_rate(client):
    """Тест получения текущей процентной ставки."""
    response = client.get('/manager_panel', query_string={'user_id': 0}, follow_redirects=True)
    assert response.status_code == 200
    assert '5.0' in response.data.decode('utf-8')  # Глобальная ставка
