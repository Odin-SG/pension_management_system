from .views import create_app

app = create_app()

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