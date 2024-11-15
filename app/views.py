from flask import Flask, render_template


# Создание приложения Flask
app = Flask(__name__)
app.config.from_object('app.config.Config')

# Главная страница
@app.route('/')
def index():
    return render_template('index.html', title='Управление Пенсионными Накоплениями')


# Страница регистрации пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('404.html'), 404


# Страница входа пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('404.html'), 404


# Личный кабинет пользователя
@app.route('/dashboard')
def dashboard():
    return render_template('404.html'), 404


# API для получения информации о накоплениях
@app.route('/api/pension', methods=['GET'])
def get_pension_data():
    return render_template('404.html'), 404


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
