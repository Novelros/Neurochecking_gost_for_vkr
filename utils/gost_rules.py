from config import GOST_PARAMS
from utils.validation import validate_date


def check_gost_compliance(form_data):
    errors = []

        # Проверка основных параметров
    if form_data['Шрифт'] != GOST_PARAMS['Шрифт']:
        errors.append(f"Шрифт должен быть '{GOST_PARAMS['Шрифт']}'")

    if form_data['Размер шрифта'] != GOST_PARAMS['Размер шрифта']:
        errors.append(f"Размер шрифта должен быть {GOST_PARAMS['Размер шрифта']}")

    if not validate_date(form_data['Дата создания']):
        errors.append("Неверный формат даты. Используйте ДД.ММ.ГГГГ")

        # Проверка полей
    margin_checks = [
        ('Верхнее поле (см)', form_data['Верхнее поле (см)'], GOST_PARAMS['Верхнее поле (см)']),
        ('Нижнее поле (см)', form_data['Нижнее поле (см)'], GOST_PARAMS['Нижнее поле (см)']),
        ('Левое поле (см)', form_data['Левое поле (см)'], GOST_PARAMS['Левое поле (см)']),
        ('Правое поле (см)', form_data['Правое поле (см)'], GOST_PARAMS['Правое поле (см)']),
        ('Межстрочный интервал', form_data['Межстрочный интервал'], GOST_PARAMS['Межстрочный интервал']),
        ('Отступ абзаца (см)', form_data['Отступ абзаца (см)'], GOST_PARAMS['Отступ абзаца (см)'])
    ]

    for name, value, expected in margin_checks:
        if abs(value - expected) > 0.05:
            errors.append(f"{name} должно быть {expected} ± 0.05")

    # Проверка обязательных элементов
    if not form_data['Наличие колонтитулов']:
        errors.append("Требуются колонтитулы")
    if not form_data['Наличие нумерации страниц']:
        errors.append("Требуется нумерация страниц")
    if not form_data['Наличие титульного листа']:
        errors.append("Требуется титульный лист")

    return errors