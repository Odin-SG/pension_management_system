from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Инициализация базы данных
db = SQLAlchemy()


# Модель пользователя
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(10), nullable=False, default='user')  # Поле роли: 'admin' или 'user'

    pension_funds = db.relationship('PensionFund', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


# Модель пенсионных накоплений
class PensionFund(db.Model):
    __tablename__ = 'pension_funds'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    contribution_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PensionFund User ID {self.user_id} Amount {self.amount}>'


class InterestRate(db.Model):
    __tablename__ = 'interest_rate'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, default=0)  # user_id = 0 означает глобальная ставка
    rate = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<InterestRate User ID {self.user_id} Rate {self.rate}>'


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Report {self.filename}>'


class Stock(db.Model):
    __tablename__ = 'stocks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    ticker = db.Column(db.String(10), nullable=False, unique=True)
    current_price = db.Column(db.Float, nullable=False)
    trend = db.Column(db.Float, default=0.0)  # Например, +0.1 для растущего тренда

    def __repr__(self):
        return f'<Stock {self.ticker} - {self.current_price}>'


class Investment(db.Model):
    __tablename__ = 'investments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # Количество акций
    invested_amount = db.Column(db.Float, nullable=False)  # Общая сумма инвестиций
