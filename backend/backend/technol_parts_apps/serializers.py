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
from users.serializers import AbstractUserSerializer


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
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(
                1,
                message='Количество ингредиента не может быть меньше единицы'
            )
        ],
        write_only=True
    )

    class Meta:
        model = Ingredient
        fields = ('id', 'amount', )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['amount'] = instance.ingredient_recipes.last().amount
        return representation


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
    ingredients = RecipeIngredientSerializer(
        many=True
    )

    class Meta:
        model = Recipe
        fields = [
            'image', 'name', 'text', 'cooking_time', 'tags', 'ingredients'
        ]

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        tags = validated_data.pop('tag')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            tag_object = get_object_or_404(Tag, pk=tag.id)
            RecipeTag.objects.create(recipe=recipe, tag=tag_object)
        for values in ingredients:
            RecipeIngredient.objects.create(
                ingredient=values['id'],
                recipe=recipe,
                amount=values['amount']
            )
        return recipe


class UserSerializer(AbstractUserSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'avatar'
        )
        read_only_fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'avatar'
        )


class GetRetrieveRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializers(many=True, source='tag')
    author = UserSerializer()
    ingredients = IngredientSerializers(many=True)
    text = serializers.CharField(source='description')

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time'
        )
        read_only_fields = (
            'id', 'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time'
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = self.context['request'].user
        if representation['ingredients']:
            for ingredient in representation['ingredients']:
                ingredient['amount'] = RecipeIngredient.objects.get(
                    recipe__id=instance.id,
                    ingredient__id=int(ingredient['id'])).amount
        if representation['author']:
            representation['author']['is_subscribed'] = user.follower.filter(
                following__exact=int(representation['author']['id'])
            ).exists()
        representation["is_favorited"] = user.favourites.filter(
            recipe__exact=instance
        ).exists()
        representation["is_in_shopping_cart"] = user.shoppings.filter(
            recipe__exact=instance
        ).exists()
        return representation
