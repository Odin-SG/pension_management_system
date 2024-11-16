from .config import Config
from .models import db, User, PensionFund
from .views import create_app
from .controllers.pension_calculator import calculate_pension
from .controllers.user_management import register_user, authenticate_user
from .utils.filters import format_currency

app = create_app()

app.jinja_env.filters['format_currency'] = format_currency

# Настройка и инициализация базы данных
with app.app_context():
    db.create_all()

    # На самом деле есть вариант проще, но в индивидуальном задании было условие об
    # обязательном использовании SQL-ной БД. Это демонстрация, что база поддерживает SQL
    result = db.engine.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
    ).fetchone()

    if result:
        admin_exists = db.engine.execute(
            "SELECT 1 FROM users WHERE role = 'admin' LIMIT 1;"
        ).fetchone()

        if not admin_exists:
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Пользователь-администратор создан с логином 'admin' и паролем 'admin123'.")
    else:
        print("Таблица 'users' не существует.")

__all__ = [
    'Config',
    'db',
    'User',
    'PensionFund',
    'calculate_pension',
    'register_user',
    'authenticate_user',
    'generate_report',
    'create_app',
    'app'
]