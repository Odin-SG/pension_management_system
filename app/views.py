from flask import Flask, render_template, request, redirect, url_for, flash, session
from .models import db, User, PensionFund
from .controllers.pension_calculator import calculate_pension, calculate_projected_return
from .controllers.user_management import register_user, authenticate_user, admin_required
from datetime import datetime

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

        user = authenticate_user(username, password)
        if user:
            # Сохраняем имя пользователя и роль в сессии
            session['username'] = user.username
            session['role'] = user.role  # Используем роль из объекта пользователя
            flash('Успешный вход!', 'success')
            print(f"Logged in as: {session.get('username')}, Role: {session.get('role')}")  # Отладка
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')

    return render_template('login.html', title='Вход')


@app.route('/logout')
def logout():
    """
    Выход пользователя из системы, очистка сессии.
    """
    session.pop('username', None)
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(url_for('login'))


# Личный кабинет пользователя
@app.route('/dashboard')
def dashboard():
    # Предположим, что данные пользователя находятся в сессии (например, после авторизации)
    username = session.get('username', 'Гость')
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('Пожалуйста, войдите в систему, чтобы получить доступ к личному кабинету.', 'danger')
        return redirect(url_for('login'))

    # Получаем пенсионные данные из базы данных
    pension_data = calculate_pension(user_id=user.id)
    total_amount = pension_data['total_amount']
    details = pension_data['details']

    # Рассчитываем прогнозируемую доходность
    years = 10
    interest_rate = 5.0  # Процентная ставка
    projected_data = calculate_projected_return(user_id=user.id, interest_rate=interest_rate / 100, years=years)
    projected_return = projected_data['projected_return']

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


@app.route('/contribute', methods=['POST'])
def contribute():
    """
    Внесение средств в пенсионные накопления пользователя.
    """
    # Получаем данные пользователя из сессии
    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('Пожалуйста, войдите в систему, чтобы сделать вклад.', 'danger')
        return redirect(url_for('login'))

    # Получаем сумму вклада из формы
    amount = float(request.form.get('amount'))
    if amount <= 0:
        flash('Сумма вклада должна быть положительной.', 'danger')
        return redirect(url_for('dashboard'))

    # Создаем новую запись вклада в пенсионный фонд
    new_contribution = PensionFund(user_id=user.id, amount=amount)
    try:
        db.session.add(new_contribution)
        db.session.commit()
        flash('Вклад успешно внесен!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при внесении вклада. Пожалуйста, попробуйте снова.', 'danger')

    return redirect(url_for('dashboard'))


@app.route('/withdraw', methods=['POST'])
def withdraw():
    """
    Снятие средств из пенсионных накоплений пользователя.
    """
    # Получаем данные пользователя из сессии
    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('Пожалуйста, войдите в систему, чтобы снять средства.', 'danger')
        return redirect(url_for('login'))

    # Получаем сумму снятия из формы
    amount = float(request.form.get('amount'))
    if amount <= 0:
        flash('Сумма снятия должна быть положительной.', 'danger')
        return redirect(url_for('dashboard'))

    # Проверка, что у пользователя достаточно средств для снятия
    total_amount = sum(fund.amount for fund in user.pension_funds)
    if amount > total_amount:
        flash('Недостаточно средств для снятия.', 'danger')
        return redirect(url_for('dashboard'))

    # Добавляем запись о снятии средств в виде отрицательной транзакции
    new_withdrawal = PensionFund(user_id=user.id, amount=-amount, contribution_date=datetime.utcnow())
    try:
        db.session.add(new_withdrawal)
        db.session.commit()
        flash('Снятие средств успешно выполнено!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при снятии средств. Пожалуйста, попробуйте снова.', 'danger')

    return redirect(url_for('dashboard'))


@app.route('/admin_panel', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    """
    Панель администратора для отображения всех пользователей и их данных.
    """
    # Получение всех пользователей и их пенсионных накоплений
    users = User.query.all()
    user_data = []
    for user in users:
        total_amount = sum(fund.amount for fund in user.pension_funds)
        user_data.append({
            'id': user.id,
            'username': user.username,
            'total_amount': total_amount
        })

    # Редактирование данных пользователя
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_username = request.form.get('new_username')
        new_role = request.form.get('new_role')
        new_amount = float(request.form.get('new_amount', 0))

        user_to_edit = User.query.get(user_id)
        if user_to_edit:
            if new_username:
                user_to_edit.username = new_username
            if new_role in ['admin', 'user']:
                user_to_edit.role = new_role

            # Обновление накоплений пользователя (новый вклад)
            if new_amount != 0:
                new_contribution = PensionFund(user_id=user_to_edit.id, amount=new_amount, contribution_date=datetime.utcnow())
                db.session.add(new_contribution)

            try:
                db.session.commit()
                flash('Данные пользователя успешно обновлены.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Ошибка при обновлении данных пользователя. Пожалуйста, попробуйте снова.', 'danger')

    # Запрос информации по конкретному пользователю
    user_id = request.args.get('user_id')
    specific_user = None
    user_history = None
    if user_id:
        specific_user = User.query.get(user_id)
        if specific_user:
            total_amount = sum(fund.amount for fund in specific_user.pension_funds)
            user_history = [
                {
                    'amount': fund.amount,
                    'contribution_date': fund.contribution_date.strftime('%Y-%m-%d')
                } for fund in specific_user.pension_funds
            ]
            specific_user = {
                'id': specific_user.id,
                'username': specific_user.username,
                'total_amount': total_amount,
                'role': specific_user.role
            }

    return render_template('admin_panel.html',
                           title='Панель Администратора',
                           users=user_data,
                           specific_user=specific_user,
                           user_history=user_history)


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


def create_app():
    return app
