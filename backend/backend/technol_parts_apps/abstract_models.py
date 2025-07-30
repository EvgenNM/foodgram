from django.contrib.auth import get_user_model
from django.db import models

import technol_parts_apps.constants as const


User = get_user_model()


class NameFieldModelBase(models.Model):
    """Абстрактный класс для моделей."""
    name = models.CharField(
        verbose_name='Название',
        max_length=const.MAX_LENGTH_NAME,
        unique=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name[:const.LENGTH_TEXT]

