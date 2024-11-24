from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User
from flask import session, redirect, url_for, flash
from functools import wraps


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
    :return: Объект пользователя, если аутентификация успешна, иначе None
    """
    # Находим пользователя по имени
    user = User.query.filter_by(username=username).first()

    # Проверяем пароль
    if user and check_password_hash(user.password_hash, password):
        return user  # Возвращаем объект пользователя

    # Если пользователь не найден или пароль неверный
    return None


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему для доступа к этой странице.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = session.get('role')
        if user_role != 'admin':
            flash('Доступ разрешен только администраторам.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = session.get('role')
        if user_role != 'manager':
            flash('Доступ разрешен только менеджерам.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


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
