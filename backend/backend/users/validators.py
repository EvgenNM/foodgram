from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

re_validator_username = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message="Поле 'username' должно состоять только из букв, цифр "
            "и символов: '@', '.', '+', '-', '_'"
)


validator_username_on_me = RegexValidator(
    regex=r'^me$',
    message='Нельзя создать пользователя с никнеймом "me"',
    inverse_match=True
)


def validator_password(value):
    if len(value) < 8:
        raise ValidationError(
            'Пароль не может быть меньше 8 символов'
        )
    if value.isdigit():
        raise ValidationError(
            'Пароль не может состоять только из цифр'
        )
    if not any(simbol.isupper() for simbol in value):
        raise ValidationError(
            'Пароль не может состоять только маленьких букв'
        )
