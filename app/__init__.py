from .config import Config
from .models import db, User, PensionFund, InterestRate
from .views import create_app
from .controllers.pension_calculator import calculate_pension
from .controllers.user_management import register_user, authenticate_user
from .utils.filters import format_currency
from .controllers.stock import create_data

app = create_app()

# Регистрация пользовательских фильтров
app.jinja_env.filters['format_currency'] = format_currency

# Настройка и инициализация базы данных
with app.app_context():
    db.create_all()
    create_data(app)

    # Демонстрация поддержки SQL
    result = db.engine.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
    ).fetchone()

    if result:
        admin_exists = db.engine.execute(
            "SELECT 1 FROM users WHERE role = 'admin' LIMIT 1;"
        ).fetchone()
        manager_exists = db.engine.execute(
            "SELECT 1 FROM users WHERE role = 'manager' LIMIT 1;"
        ).fetchone()
        usr_exists = db.engine.execute(
            "SELECT 1 FROM users WHERE role = 'user' LIMIT 1;"
        ).fetchone()

        if not admin_exists:
            admin_user = User(username='admin', role='admin')
            admin_user.set_password('admin')
            db.session.add(admin_user)
        if not manager_exists:
            manager_user = User(username='manager', role='manager')
            manager_user.set_password('manager')
            db.session.add(manager_user)
        if not usr_exists:
            usr_user = User(username='user', role='user')
            usr_user.set_password('user')
            db.session.add(usr_user)


    # Проверка на существование глобальной ставки
    global_rate = InterestRate.query.filter_by(user_id=0).first()
    if not global_rate:
        global_rate = InterestRate(user_id=0, rate=5.0)  # Устанавливаем базовую ставку 5.0%
        db.session.add(global_rate)
        print("Глобальная процентная ставка создана: 5.0%.")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при инициализации базы данных: {str(e)}")

__all__ = [
    'Config',
    'db',
    'User',
    'PensionFund',
    'InterestRate',
    'calculate_pension',
    'register_user',
    'authenticate_user',
    'generate_report',
    'create_app',
    'app'
]
