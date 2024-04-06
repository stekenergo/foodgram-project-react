from django.core.exceptions import ValidationError


def validate_username(value):
    if not isinstance(value, str):
        raise ValidationError('username должен иметь тип: строка')
    return value
