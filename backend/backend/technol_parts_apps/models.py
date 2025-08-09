from django.contrib.auth import get_user_model
from django.db import models

import technol_parts_apps.constants as const
import technol_parts_apps.validators as vd
from .abstract_models import NameFieldModelBase

User = get_user_model()


class Recipe(NameFieldModelBase):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes')
    image = models.ImageField(
        upload_to='recipes/', null=True, blank=True
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )
    description = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки',
        validators=vd.cooking_time_validators
    )
    ingredients = models.ManyToManyField(
        'Ingredient', through='RecipeIngredient', null=True, blank=True
    )
    tags = models.ManyToManyField(
        'Tag', through='RecipeTag', null=True, blank=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'Рецепт {self.name[:const.LENGTH_TEXT]} от {self.author}'


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


class RecipeTag(models.Model):
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name='tag_recipes'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipe_tags'
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'
        ordering = ('tag', )

    def __str__(self):
        return (
            f'Тег {self.tag} '
            f'рецепта {self.recipe}'
        )


class RecipeIngredient(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='recipes_ingredient',
        null=True, blank=True,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количественный показатель ингридиента',
        validators=vd.amount_validators
    )
    date = models.DateTimeField(
        verbose_name='Дата изменения',
        auto_now=True,
        null=True, blank=True,
    )

    class Meta:
        verbose_name = 'Количество ингридиентов'
        verbose_name_plural = 'Количество ингридиентов'
        ordering = ('date', )

    def __str__(self):
        return (
            f'{self.ingredient} '
            f'{self.recipe}'
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
        ordering = ('user', )

    def __str__(self):
        return (
            f'Подписка {self.user} на {self.following}'
        )


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
        ordering = ('user', )

    def __str__(self):
        return (
            f'Лист избаннго {self.user}'
        )


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
        ordering = ('user', )

    def __str__(self):
        return (
            f'Лист покупок {self.user}'
        )
