from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from django.core.validators import MinValueValidator
import users.validators as vd
import technol_parts_apps.constants as const
import base64
import time
import re

from django.core.files.base import ContentFile
from .models import (
    Follow, Tag, Ingredient, Recipe, RecipeIngredient, RecipeTag
)


User = get_user_model()


class TagSerializers(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=const.LENGTH_CONST,
        read_only=True,
    )
    slug = serializers.CharField(
        max_length=const.MAX_LENGTH_SLUG,
        read_only=True,
    )

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', )


# class RecipeTag(serializers.ModelSerializer):

#     class Meta:
#         model = Tag
#         fields = ('id', 'name', 'slug', )


class IngredientSerializers(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )
    following = serializers.SlugRelatedField(
        # slug_field='username',
        slug_field='id',
        queryset=User.objects.all(),
        error_messages={
            'does_not_exist': 'Учетные данные не были предоставлены вообще.'
        },
    )

    class Meta:
        model = Follow
        fields = ('user', 'following',)

    def validate(self, data):
        data['user'] = self.context['request'].user
        if data['user'].follower.filter(
            following__exact=data['following']
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )
        if data['following'] == data['user']:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя (даже если очень хочется).'
            )
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='image.' + ext)

        return super().to_internal_value(data)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id_ingredient = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient'
    )
    amount = serializers.IntegerField(
        source='count',
        validators=[
            MinValueValidator(
                1,
                message='Количество ингредиента не может быть меньше единицы'
            )
        ]
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id_ingredient', 'amount', )


class CreateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)
    name = serializers.CharField(
        max_length=const.RECIPE_NAME_LENGTH,
        required=True,
    )
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(
                1,
                message='Время готовки не может быть меньше 1 минуты'
            )
        ]
    )
    text = serializers.CharField(
        source='description',
        max_length=const.TEXT_LENGTH
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        source='tag',
    )

    class Meta:
        model = Recipe
        fields = [
            'image', 'name', 'text', 'cooking_time', 'tags'
        ]

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        tags = validated_data.pop('tag')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            tag_object = get_object_or_404(Tag, pk=tag.id)
            RecipeTag.objects.create(recipe=recipe, tag=tag_object)
        return recipe
