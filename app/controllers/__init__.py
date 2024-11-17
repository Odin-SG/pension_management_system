from .generate_report import generate_user_report, get_report_path
from .pension_calculator import calculate_pension
from .stock import update_stock_prices, create_data
from .user_management import register_user, authenticate_user

# Экспортирование всех контроллеров для удобного использования в других частях приложения
__all__ = [
    'calculate_pension',
    'register_user',
    'authenticate_user',
    'generate_report',
    'generate_user_report',
    'get_report_path',
    'update_stock_prices',
    'create_data'
]
