from django.core.exceptions import ValidationError


def validate_username(value):
    if not isinstance(value, str):
        raise ValidationError('username должен иметь тип: строка')
    if value == 'Me':
        raise ValidationError('Имя пользователя не может быть "Me"')
    if value.lower() == 'me':
        raise ValidationError('Имя пользователя не может быть "me"')
    return value
