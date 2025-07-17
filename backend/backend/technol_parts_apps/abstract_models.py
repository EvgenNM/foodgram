from django.contrib.auth import get_user_model
from django.db import models

import technol_parts_apps.constants as const
# from .models import Recipe


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


class FavoriteAndShoppingListModel(models.Model):
    pass
    # user = models.ForeignKey(
    #     User, on_delete=models.CASCADE, related_name='favourites'
    # )
    # recipe = models.ForeignKey(
    #     Recipe, on_delete=models.CASCADE, related_name='recipes'
    # )

    # class Meta:
    #     abstract = True
