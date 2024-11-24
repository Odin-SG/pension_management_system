import pytest
from app import create_app, db
from app.models import User
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
            yield client

        import os
        if os.path.exists(db_path):
            os.remove(db_path)


def test_register_user_success(client):
    """Позитивный тест успешной регистрации нового пользователя."""
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'validpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Регистрация прошла успешно!' in response.data.decode('utf-8')

    # Проверяем, что пользователь добавлен в базу данных
    user = User.query.filter_by(username='newuser').first()
    assert user is not None
    assert user.username == 'newuser'


def test_register_existing_user(client):
    """Негативный тест регистрации с существующим именем пользователя."""
    # Добавляем пользователя в базу данных
    user = User(username='existinguser')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

    # Попытка зарегистрировать пользователя с таким же именем
    response = client.post('/register', data={
        'username': 'existinguser',
        'password': 'newpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Ошибка регистрации. Возможно, пользователь уже существует.' in response.data.decode('utf-8')

    # Убедимся, что количество пользователей с данным именем не изменилось
    users = User.query.filter_by(username='existinguser').all()
    assert len(users) == 1


def test_register_short_username(client):
    """Негативный тест регистрации с коротким именем пользователя."""
    response = client.post('/register', data={
        'username': 'ab',  # Короткое имя пользователя
        'password': 'validpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Логин должен содержать не менее 3 символов.' in response.data.decode('utf-8')


def test_register_short_password(client):
    """Негативный тест регистрации с коротким паролем."""
    response = client.post('/register', data={
        'username': 'validuser',
        'password': '12'  # Короткий пароль
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Пароль должен содержать не менее 3 символов.' in response.data.decode('utf-8')


def test_register_username_with_special_characters(client):
    """Негативный тест регистрации с именем пользователя, содержащим специальные символы."""
    response = client.post('/register', data={
        'username': 'valid@user!',
        'password': 'validpassword'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Регистрация прошла успешно!' in response.data.decode('utf-8')


def test_register_success_redirect_to_login(client):
    """Позитивный тест: успешная регистрация должна перенаправить на страницу входа."""
    response = client.post('/register', data={
        'username': 'redirectuser',
        'password': 'validpassword'
    })

    assert response.status_code == 302  # Редирект
    assert '/login' in response.headers['Location']
