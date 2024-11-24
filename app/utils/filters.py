def format_currency(value):
    """
    Форматирование чисел: группировка по 3 цифры и 2 знака после запятой.
    """
    try:
        return f"{float(value):,.2f}".replace(",", " ")
    except (ValueError, TypeError):
        return value
