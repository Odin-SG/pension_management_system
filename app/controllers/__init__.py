from .pension_calculator import calculate_pension
from .user_management import register_user, authenticate_user

# Экспортирование всех контроллеров для удобного использования в других частях приложения
__all__ = [
    'calculate_pension',
    'register_user',
    'authenticate_user',
    'generate_report'
]
