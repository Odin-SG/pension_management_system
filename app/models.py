from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Инициализация базы данных
db = SQLAlchemy()


# Модель пользователя
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pension_funds = db.relationship('PensionFund', backref='user', lazy=True)

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
