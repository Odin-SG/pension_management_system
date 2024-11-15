from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User


# Функция для регистрации нового пользователя
def register_user(username, password):
    """
    Регистрация нового пользователя.

    :param username: Имя пользователя
    :param password: Пароль пользователя
    :return: True, если регистрация успешна, иначе False
    """
    if User.query.filter_by(username=username).first():
        # Пользователь с таким именем уже существует
        return False

    password_hash = generate_password_hash(password)
    new_user = User(username=username, password_hash=password_hash)

    try:
        db.session.add(new_user)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False


# Функция для аутентификации пользователя
def authenticate_user(username, password):
    """
    Аутентификация пользователя.

    :param username: Имя пользователя
    :param password: Пароль пользователя
    :return: True, если аутентификация успешна, иначе False
    """
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return True
    return False


# Функция для обновления данных пользователя
def update_user_password(user_id, new_password):
    """
    Обновление пароля пользователя.

    :param user_id: Идентификатор пользователя
    :param new_password: Новый пароль
    :return: True, если обновление успешно, иначе False
    """
    user = User.query.get(user_id)
    if user:
        try:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False
    return False
