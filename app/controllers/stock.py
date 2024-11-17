import random
from time import sleep
from datetime import datetime
from app import db
from app.models import Stock, StockPriceHistory

def update_stock_prices(app):
    """
    Эмуляция рынка: обновление котировок акций.
    """
    print("Update stock is started at new thread\n")
    with app.app_context():
        while True:
            stocks = Stock.query.all()
            for stock in stocks:
                change = random.uniform(-0.5, 0.5) * (1 + abs(stock.trend))
                stock.current_price = max(1.0, stock.current_price + change)

                if random.random() < 0.1:  # 10% вероятность смены тренда
                    stock.trend = random.uniform(-0.2, 0.2)

                price_history = StockPriceHistory(
                    stock_id=stock.id,
                    timestamp=datetime.utcnow(),
                    price=stock.current_price
                )
                db.session.add(price_history)

            # Сохраняем изменения
            db.session.commit()
            sleep(1)


def create_data(app):
    """
    Создание данных для акций и истории цен.
    """
    with app.app_context():
        if db.session.query(Stock).count() > 0 or db.session.query(StockPriceHistory).count() > 0:
            print("Моковые данные уже существуют. Создание пропущено.")
            return

        stocks = [
            Stock(name="Акция 1", ticker="A1", current_price=100.0),
            Stock(name="Акция 2", ticker="A2", current_price=200.0),
            Stock(name="Акция 3", ticker="A3", current_price=300.0),
        ]
        db.session.add_all(stocks)
        db.session.commit()

        now = datetime.utcnow()
        for stock in stocks:
            for i in range(10):  # Последние 10 минут
                price_history = StockPriceHistory(
                    stock_id=stock.id,
                    timestamp=now - timedelta(minutes=i),
                    price=stock.current_price + random.uniform(-5, 5)
                )
                db.session.add(price_history)

        db.session.commit()
