from datetime import datetime

def validate_date(date_str):
    """
    Проверяет корректность формата даты.
    Убеждается, что дата соответствует формату ДД.ММ.ГГГГ.
    """
    try:
        datetime.strptime(date_str, '%d.%m.%Y')
        return True
    except ValueError:
        return False

def validate_number(value, min_val, max_val):
    """
    Проверяет что числовое значение находится в допустимом диапазоне.
    Выполняет конвертацию строки в число и проверку границ.
    """
    try:
        num = float(value)
        return min_val <= num <= max_val
    except ValueError:
        return False