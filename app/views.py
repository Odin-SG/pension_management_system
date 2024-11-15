from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from .models import db, User, PensionFund
from .controllers.pension_calculator import calculate_pension
from .controllers.user_management import register_user, authenticate_user

# Создание приложения Flask
app = Flask(__name__)
app.config.from_object('app.config.Config')
db.init_app(app)


# Главная страница
@app.route('/')
def index():
    return render_template('index.html', title='Управление Пенсионными Накоплениями')


# Страница регистрации пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if register_user(username, password):
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Ошибка регистрации. Возможно, пользователь уже существует.', 'danger')
    return render_template('register.html', title='Регистрация')


# Страница входа пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if authenticate_user(username, password):
            session['username'] = username
            flash('Успешный вход!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    return render_template('login.html', title='Вход')


# Личный кабинет пользователя
@app.route('/dashboard')
def dashboard():
    # Предположим, что данные пользователя находятся в сессии (например, после авторизации)
    username = session.get('username', 'Гость')

    # Пример данных для подстановки
    total_amount = 100000  # например, общая сумма накоплений пользователя
    details = [
        {'amount': 20000, 'contribution_date': '2023-01-15'},
        {'amount': 30000, 'contribution_date': '2023-06-10'},
        {'amount': 50000, 'contribution_date': '2024-01-01'}
    ]
    years = 10
    interest_rate = 5.0
    projected_return = 200000  # предполагаемая доходность

    # Рендерим шаблон и передаем данные
    return render_template(
        'dashboard.html',
        title='Личный Кабинет',
        username=username,
        total_amount=total_amount,
        details=details,
        years=years,
        interest_rate=interest_rate,
        projected_return=projected_return
    )


# API для получения информации о накоплениях
@app.route('/api/pension', methods=['GET'])
def get_pension_data():
    user_id = request.args.get('user_id')
    user = User.query.get(user_id)
    if user:
        pension_data = calculate_pension(user_id)
        return jsonify(pension_data), 200
    return jsonify({'error': 'Пользователь не найден'}), 404


# Обработка ошибок
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# Создание экземпляра приложения

def create_app():
    return app
