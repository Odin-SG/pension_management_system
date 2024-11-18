import pytest
from flask import url_for
from app import create_app, db
from app.models import User


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Используем временную базу данных в памяти
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client


def test_register_user_success(client):
    # Тест успешной регистрации нового пользователя
    response = client.post('/register', data={'username': 'newuser', 'password': 'validpassword'},
                           follow_redirects=False)

    # Проверка кода ответа на успешный редирект на страницу логина
    assert response.status_code == 302  # Ожидаем редирект
    assert response.headers['Location'] == url_for('login', _external=False)  # Должен быть редирект на '/login'

    # Проверка, что пользователь сохранен в базе данных
    user = User.query.filter_by(username='newuser').first()
    assert user is not None
    assert user.username == 'newuser'


def test_register_user_fail(client):
    # Проверка регистрации с некорректными данными (имя пользователя и пароль менее 3 символов)
    response = client.post('/register', data={'username': 'ab', 'password': '12'}, follow_redirects=True)

    # Убедимся, что после ошибки мы остались на странице регистрации
    assert response.status_code == 200
    temp = response.data.decode('utf-8')
    assert '<title>Регистрация</title>' in response.data.decode('utf-8')


def test_register_existing_user(client):
    # Создаем пользователя в базе данных
    user = User(username='existinguser')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()

    # Попытка регистрации с уже существующим именем пользователя
    response = client.post('/register', data={'username': 'existinguser', 'password': 'testpassword'}, follow_redirects=True)

    # Проверка, что произошел редирект на страницу регистрации
    assert response.status_code == 200

    # Проверка, что количество пользователей с данным именем не увеличилось
    users = User.query.filter_by(username='existinguser').all()
    assert len(users) == 1
