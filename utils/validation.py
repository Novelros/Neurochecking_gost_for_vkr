from datetime import datetime

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%d.%m.%Y')
        return True
    except ValueError:
        return False

def validate_number(value, min_val, max_val):
    try:
        num = float(value)
        return min_val <= num <= max_val
    except ValueError:
        return False