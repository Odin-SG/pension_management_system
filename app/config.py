import os


class Config:
    """
    Основной класс конфигурации для приложения.
    """
    # Базовые настройки приложения
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'qwerty123456')  # Секретный ключ для сессий и шифрования

    # Настройки базы данных. В нашем случае sqlite
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///pension_management.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки безопасности
    BCRYPT_LOG_ROUNDS = os.getenv('BCRYPT_ROUNDS', 13)  # Число раундов хеширования паролей
    TOKEN_EXPIRATION_SECONDS = os.getenv('TOKEN_EXPIRATION_SECONDS', 3600)  # Время жизни токенов в секундах


class DevelopmentConfig(Config):
    """
    Конфигурация для разработки.
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """
    Конфигурация для прод-среды.
    """
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///pension_management_prod.db')


config_by_name = dict(
    dev=DevelopmentConfig,
    prod=ProductionConfig
)

key = Config.SECRET_KEY
