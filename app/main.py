from app.views import create_app
from threading import Thread
from app.controllers.stock import update_stock_prices

if __name__ == "__main__":
    app = create_app()
    Thread(target=update_stock_prices, args=(app,), daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=True)