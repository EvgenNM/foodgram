from django.contrib.auth.models import AbstractUser
from django.db import models

import users.constants as const
import users.validators as vd


class User(AbstractUser):
    """"Кастомная модель пользователя"""
    email = models.EmailField(
        verbose_name='Email пользователя',
        max_length=const.EMAIL_FIELD_LENGTH,
        unique=True
    )
    username = models.CharField(
        verbose_name='Никнейм пользователя',
        max_length=const.USERNAME_LENGTH,
        unique=True,
        validators=[vd.re_validator_username, vd.validator_username_on_me]
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=const.FIRST_NAME_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=const.LAST_NAME_LENGTH,
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=const.PASSWORD_LENGTH,
        validators=[vd.validator_password]
    )
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        default=None
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:const.USERNAME_LENGTH_STR]