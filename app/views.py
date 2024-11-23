from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from .controllers.generate_report import PDFReport, generate_user_report, get_report_path
from .models import db, User, PensionFund, InterestRate, Report, Investment, Stock, StockPriceHistory
from .controllers.pension_calculator import calculate_pension, calculate_projected_return
from .controllers.user_management import register_user, authenticate_user, admin_required, manager_required, \
    login_required
from datetime import datetime, timedelta

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
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Проверка на минимальную длину логина и пароля
        if len(username) < 3:
            flash('Логин должен содержать не менее 3 символов.', 'danger')
            return render_template('register.html', title='Регистрация')
        if len(password) < 3:
            flash('Пароль должен содержать не менее 3 символов.', 'danger')
            return render_template('register.html', title='Регистрация')

        if register_user(username, password):
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Ошибка регистрации. Возможно, пользователь уже существует.', 'danger')
    return render_template('register.html', title='Регистрация')



# Страница входа пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Проверяем, есть ли пользователь уже в сессии
    if 'username' in session:
        return redirect(url_for('dashboard'))

    # Обработка POST-запроса (попытка входа)
    if request.method == 'POST':
        username = request.form.get('username') if not request.is_json else request.json.get('username')
        password = request.form.get('password') if not request.is_json else request.json.get('password')

        # Проверка аутентификации пользователя
        user = authenticate_user(username, password)
        if user:
            # Сохраняем имя пользователя и роль в сессии
            session['username'] = user.username
            session['role'] = user.role
            session['user_id'] = user.id
            print(f"Logged in as: {session.get('username')}, Role: {session.get('role')}")  # Отладка

            if request.is_json:
                # Если это AJAX запрос, возвращаем JSON с успехом
                return jsonify(success=True)
            else:
                # Если это обычный POST, перенаправляем на дашборд
                return redirect(url_for('dashboard'))
        else:
            if request.is_json:
                # Возвращаем JSON-ответ с ошибкой, если это AJAX запрос
                return jsonify(success=False, message='Неверное имя пользователя или пароль.'), 400
            else:
                # Если это обычный POST, возвращаем ошибку через Flash и остаемся на странице
                flash('Неверное имя пользователя или пароль.', 'danger')

    # Если метод GET — отображаем форму для входа
    return render_template('login.html', title='Вход')


@app.route('/logout')
@login_required
def logout():
    """
    Выход пользователя из системы, очистка сессии.
    """
    session.pop('username', None)
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(url_for('login'))


# Личный кабинет пользователя
@app.route('/dashboard')
@login_required
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
    interest_rate_entry = InterestRate.query.filter_by(user_id=user.id).first()
    if interest_rate_entry:
        interest_rate = interest_rate_entry.rate
    else:
        global_rate_entry = InterestRate.query.filter_by(user_id=0).first()
        interest_rate = global_rate_entry.rate

    years = 10
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
@login_required
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
@login_required
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
    Панель администратора для управления пользователями и их данными.
    """

    if request.method == 'POST':
        # Асинхронное редактирование данных пользователя
        data = request.get_json()  # Получаем JSON-данные от клиента
        user_id = data.get('user_id')
        new_username = data.get('new_username')
        new_role = data.get('new_role')
        new_amount = float(data.get('new_amount', 0))

        user_to_edit = User.query.get(user_id)
        if user_to_edit:
            # Обновляем данные пользователя
            if new_username:
                user_to_edit.username = new_username
            if new_role in ['admin', 'user', 'manager']:
                user_to_edit.role = new_role
            if new_amount != 0:
                new_contribution = PensionFund(
                    user_id=user_to_edit.id,
                    amount=new_amount,
                    contribution_date=datetime.utcnow()
                )
                db.session.add(new_contribution)

            try:
                db.session.commit()
                return jsonify(success=True), 200
            except Exception as e:
                db.session.rollback()
                return jsonify(success=False, error=str(e)), 500
        return jsonify(success=False, error="Пользователь не найден"), 404

    # Обработка GET-запросов
    user_id = request.args.get('user_id')
    if user_id:
        # Получение информации о конкретном пользователе
        specific_user = User.query.get(user_id)
        if specific_user:
            total_amount = sum(fund.amount for fund in specific_user.pension_funds)
            user_history = [
                {
                    'amount': fund.amount,
                    'contribution_date': fund.contribution_date.strftime('%Y-%m-%d')
                } for fund in specific_user.pension_funds
            ]
            return jsonify(specific_user={
                'id': specific_user.id,
                'username': specific_user.username,
                'total_amount': total_amount,
                'role': specific_user.role
            }, user_history=user_history)

    # Получение всех пользователей и их пенсионных накоплений для отображения в таблице
    users = User.query.all()
    user_data = [
        {
            'id': user.id,
            'username': user.username,
            'total_amount': sum(fund.amount for fund in user.pension_funds)
        } for user in users
    ]
    return render_template('admin_panel.html',
                           title='Панель Администратора',
                           users=user_data)


@app.route('/manager_panel', methods=['GET', 'POST'])
@manager_required
def manager_panel():
    """
    Регулирование годовой процентной ставки по вкладу для конкретного пользователя. Доступно только менеджерам.
    """
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_rate = float(request.form.get('interest_rate'))
        if new_rate <= 0:
            flash('Процентная ставка должна быть положительной.', 'danger')
        else:
            try:
                # Проверяем, указан ли пользователь
                if user_id:
                    user = User.query.get(user_id)
                    if user:
                        # Устанавливаем персональную процентную ставку для пользователя
                        interest_rate = InterestRate.query.filter_by(user_id=user.id).first()
                        if interest_rate:
                            interest_rate.rate = new_rate
                        else:
                            interest_rate = InterestRate(user_id=user.id, rate=new_rate)
                            db.session.add(interest_rate)
                    else:
                        flash('Пользователь не найден.', 'danger')
                        return redirect(url_for('manager_panel'))
                else:
                    # Если пользователь не указан, обновляем глобальную процентную ставку
                    interest_rate = InterestRate.query.filter_by(user_id=0).first()
                    if interest_rate:
                        interest_rate.rate = new_rate
                    else:
                        interest_rate = InterestRate(user_id=0, rate=new_rate)
                        db.session.add(interest_rate)

                db.session.commit()
                flash('Процентная ставка успешно обновлена.', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Ошибка при обновлении процентной ставки. Пожалуйста, попробуйте снова.', 'danger')
    # Получаем текущую процентную ставку для отображения на странице
    user_id = request.args.get('user_id')
    current_rate = None
    if user_id:
        interest_rate = InterestRate.query.filter_by(user_id=user_id).first()
        if interest_rate:
            current_rate = interest_rate.rate
        else:
            # Если для пользователя ставка не установлена, берем глобальную
            global_rate = InterestRate.query.filter_by(user_id=0).first()
            current_rate = global_rate.rate if global_rate else None
    else:
        # Если пользователь не указан, берем глобальную ставку
        global_rate = InterestRate.query.filter_by(user_id=0).first()
        current_rate = global_rate.rate if global_rate else None

    return render_template('manager_panel.html', title='Регулирование Процентной Ставки', current_rate=current_rate)


# Эндпоинт для отображения всех существующих отчетов
@app.route('/reports', methods=['GET'])
@login_required
def reports():
    """
    Эндпоинт для отображения списка отчетов или возврата их в формате JSON.
    """
    user_role = session.get('role')
    user_id = session.get('user_id')

    if user_role == 'admin':
        reports = Report.query.all()
    else:
        reports = Report.query.filter_by(user_id=user_id).all()

    reports_list = [
        {
            'report_id': report.id,
            'user_id': report.user_id,
            'filename': report.filename,
            'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for report in reports
    ]

    # Если запрос сделан с ожидаемым JSON-ответом
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(reports=reports_list)

    # Иначе возвращаем страницу
    return render_template('reports.html', title='Список Отчетов', reports=reports_list)


# Эндпоинт для генерации отчета по накоплениям пользователя
@app.route('/generate_report', methods=['GET'])
@login_required
def generate_report():
    """
    Эндпоинт для генерации отчета по накоплениям пользователя в формате PDF.
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify(success=False, error="ID пользователя не предоставлен"), 400

    report_path, error = generate_user_report(user_id)
    if error:
        return jsonify(success=False, error=error), 500

    return jsonify(success=True, message="Отчет успешно сгенерирован")


# Эндпоинт для загрузки сохраненного отчета
@app.route('/download_report', methods=['GET'])
@login_required
def download_report():
    """
    Эндпоинт для загрузки сохраненного отчета по его ID.
    """
    report_id = request.args.get('report_id')
    if not report_id:
        flash('ID отчета не предоставлен.', 'danger')
        return redirect(url_for('reports'))

    report_path, error = get_report_path(report_id)
    if error:
        flash(error, 'danger')
        return redirect(url_for('reports'))

    return send_file(report_path, as_attachment=True, download_name=report_path.split('/')[-1])


@app.route('/investments', methods=['GET'])
@login_required
def investments():
    """
    Страница инвестиций: отображение доступных акций и текущего портфеля пользователя.
    """
    user_id = session.get('user_id')

    # Доступные акции
    stocks = Stock.query.all()

    # Инвестиции пользователя
    investments = Investment.query.filter_by(user_id=user_id).all()
    investment_data = []
    for investment in investments:
        stock = investment.stock
        average_price = investment.invested_amount / investment.quantity
        investment_data.append({
            'quantity': investment.quantity,
            'stock_name': stock.name,
            'total_amount': f"{investment.invested_amount:,.2f}".replace(',', ' '),
            'ticker': stock.ticker,
            'average_price': f"{average_price:,.2f}".replace(',', ' '),
            'stock_id': investment.stock_id
        })

    return render_template('investments.html', stocks=stocks, investments=investment_data)


@app.route('/get_prices', methods=['GET'])
def get_prices():
    """
    Возвращает текущие цены на акции.
    """
    stocks = Stock.query.all()
    prices = [
        {'ticker': stock.ticker, 'price': stock.current_price}
        for stock in stocks
    ]
    return jsonify(prices)


@app.route('/buy_stock', methods=['POST'])
@login_required
def buy_stock():
    """
    Покупка акций с использованием транзакционной системы.
    """
    user_id = session.get('user_id')
    stock_id = request.form.get('stock_id')
    quantity = float(request.form.get('quantity'))

    # Получаем информацию об акции
    stock = Stock.query.get(stock_id)
    if not stock:
        flash('Акция не найдена.', 'danger')
        return redirect(url_for('investments'))

    # Рассчитываем общую стоимость
    total_cost = stock.current_price * quantity

    # Рассчитываем доступный баланс пользователя
    funds = PensionFund.query.filter_by(user_id=user_id).all()
    available_balance = sum(fund.amount for fund in funds)

    if available_balance < total_cost:
        flash('Недостаточно средств для покупки акций.', 'danger')
        return redirect(url_for('investments'))

    # Списываем деньги из доступных средств (создаём запись с отрицательной суммой)
    new_transaction = PensionFund(
        user_id=user_id,
        amount=-total_cost,
        contribution_date=datetime.utcnow()
    )
    db.session.add(new_transaction)

    # Добавляем акции в портфель пользователя
    investment = Investment.query.filter_by(user_id=user_id, stock_id=stock_id).first()
    if investment:
        investment.quantity += quantity
        investment.invested_amount += total_cost
    else:
        investment = Investment(
            user_id=user_id,
            stock_id=stock_id,
            quantity=quantity,
            invested_amount=total_cost
        )
        db.session.add(investment)

    # Сохраняем изменения
    try:
        db.session.commit()
        flash('Акции успешно куплены.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при покупке акций. Попробуйте снова.', 'danger')

    return redirect(url_for('investments'))


@app.route('/sell_stock', methods=['POST'])
@login_required
def sell_stock():
    """
    Продажа акций.
    """
    user_id = session.get('user_id')
    stock_id = request.form.get('stock_id')  # Получаем ID акции из запроса
    quantity_to_sell = float(request.form.get('quantity'))  # Количество акций для продажи

    # Получаем информацию об инвестициях
    investment = Investment.query.filter_by(user_id=user_id, stock_id=stock_id).first()
    if not investment or investment.quantity < quantity_to_sell:
        return jsonify({'success': False, 'message': 'Недостаточно акций для продажи.'}), 400

    # Получаем информацию об акции
    stock = Stock.query.get(stock_id)
    if not stock:
        return jsonify({'success': False, 'message': 'Акция не найдена.'}), 404

    # Рассчитываем доход от продажи
    total_income = stock.current_price * quantity_to_sell

    # Обновляем инвестиции
    investment.quantity -= quantity_to_sell
    investment.invested_amount -= total_income
    if investment.quantity == 0:
        db.session.delete(investment)  # Удаляем инвестицию, если количество акций = 0

    # Добавляем запись в транзакции
    new_transaction = PensionFund(
        user_id=user_id,
        amount=total_income,
        contribution_date=datetime.utcnow()
    )
    db.session.add(new_transaction)

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Акции успешно проданы!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Ошибка при продаже акций. Попробуйте снова.'}), 500



@app.route('/stock_prices/<int:stock_id>', methods=['GET'])
def stock_prices(stock_id):
    """
    Возвращает исторические данные о ценах акций в формате JSON.
    """
    hours = request.args.get('hours', default=2, type=int)
    time_limit = datetime.utcnow() - timedelta(hours=hours)

    # Фильтруем записи по stock_id и времени
    prices = StockPriceHistory.query.filter(
        StockPriceHistory.stock_id == stock_id,
        StockPriceHistory.timestamp >= time_limit
    ).order_by(StockPriceHistory.timestamp).all()

    # Формируем данные для ответа
    data = [
        {'timestamp': price.timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'price': price.price}
        for price in prices
    ]
    return jsonify(data)

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
