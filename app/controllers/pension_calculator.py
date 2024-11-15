from app.models import PensionFund


# Функция для расчета пенсионных накоплений

def calculate_pension(user_id=None):
    """
    Расчет текущих пенсионных накоплений пользователя.
    Если user_id не задан, выполняется общий расчет.
    """
    if user_id:
        funds = PensionFund.query.filter_by(user_id=user_id).all()
        total_amount = sum(fund.amount for fund in funds)
        return {
            "user_id": user_id,
            "total_amount": total_amount,
            "details": [
                {
                    "amount": fund.amount,
                    "contribution_date": fund.contribution_date.strftime('%Y-%m-%d')
                } for fund in funds
            ]
        }
    else:
        # Общий расчет для всех пользователей
        funds = PensionFund.query.all()
        total_amount = sum(fund.amount for fund in funds)
        return {
            "total_amount": total_amount,
            "count_of_users": len(set(fund.user_id for fund in funds))
        }


# Функция для расчета будущей прогнозируемой доходности

def calculate_projected_return(user_id, interest_rate, years):
    """
    Расчет будущей прогнозируемой доходности на основе текущих данных.

    :param user_id: Идентификатор пользователя
    :param interest_rate: Процентная ставка в десятичном формате (например, 0.05 для 5%)
    :param years: Количество лет, на которые рассчитывается доходность
    :return: Словарь с расчетной будущей доходностью
    """
    funds = PensionFund.query.filter_by(user_id=user_id).all()
    total_amount = sum(fund.amount for fund in funds)

    # Прогнозируемая доходность на основе сложного процента
    future_value = total_amount * ((1 + interest_rate) ** years)

    return {
        "user_id": user_id,
        "current_total": total_amount,
        "interest_rate": interest_rate,
        "years": years,
        "projected_return": future_value
    }
