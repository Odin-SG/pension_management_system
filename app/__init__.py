from .config import Config
from .models import db, User, PensionFund
from .views import create_app
from .controllers.pension_calculator import calculate_pension
from .controllers.user_management import register_user, authenticate_user

app = create_app()

# Настройка и инициализация базы данных
with app.app_context():
    db.create_all()

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