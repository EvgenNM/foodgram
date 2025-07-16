from datetime import datetime
from django.db import models
from django.contrib.auth import get_user_model

from .abstract_models import (
    NameFieldModelBase,
    # FavoriteAndShoppingListModel
    )
import technol_parts_apps.constants as const

User = get_user_model()


class Recipe(NameFieldModelBase):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')
    image = models.ImageField(
        upload_to='recipes/', null=True, blank=True)
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    description = models.TextField()
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время готовки',
    )
    ingredients = models.ManyToManyField(
        'Ingredient', through='RecipeIngredient'
    )
    tag = models.ForeignKey(
        'Tag', on_delete=models.CASCADE, related_name='tags')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)


class Ingredient(NameFieldModelBase):
    measurement_unit = models.CharField(
        verbose_name='единица измерения',
        max_length=const.MAX_LENGTH_NAME_UNIT,
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)


class Tag(NameFieldModelBase):
    slug = models.SlugField(
        verbose_name='Slug',
        max_length=const.MAX_LENGTH_SLUG,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name', )


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(
        verbose_name='Количественный показатель ингридиента',
    )

    class Meta:
        verbose_name = 'Количество ингридиентов'
        verbose_name_plural = 'Количество ингридиентов'

    def __str__(self):
        return (
            f'{self.ingredient[:const.LENGTH_CONST]} '
            f'{self.recipe[:const.LENGTH_CONST]}'
        )


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followings'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favourites'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipes'
    )

    class Meta:
        verbose_name = 'Лист избранного'
        verbose_name_plural = 'Листы избранного'


class Shopping(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shoppings'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_shops'
    )

    class Meta:
        verbose_name = 'Лист покупок'
        verbose_name_plural = 'Листы покупок'
