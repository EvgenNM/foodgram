from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from django.core.validators import MinValueValidator
import technol_parts_apps.constants as const
import base64

from django.core.files.base import ContentFile
from .models import (
    Follow, Tag, Ingredient, Recipe, RecipeIngredient, RecipeTag, Shopping, Favorite
)
from users.serializers import RetrieveUserSerializer


User = get_user_model()


class TagSerializers(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', )
        read_only_fields = ('name', 'slug', )


class IngredientSerializers(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


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
        representation['amount'] = RecipeIngredient.objects.filter(
            ingredient=instance).order_by('date').last().amount
        return representation


class CreateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    name = serializers.CharField(
        max_length=const.RECIPE_NAME_LENGTH,
    )
    cooking_time = serializers.IntegerField(
        validators=[
            MinValueValidator(
                1,
                message='Время готовки не может быть меньше 1 минуты'
            )
        ],
    )
    text = serializers.CharField(
        source='description',
        max_length=const.TEXT_LENGTH,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'image', 'name', 'text', 'cooking_time',
            'tags', 'ingredients', 'author'
        ]
        read_only_fields = ('id', 'author')

    def validate(self, data):
        if not data['ingredients']:
            raise serializers.ValidationError(
                'Поле "ingredients" не может быть пустым'
            )
        if not data['tags']:
            raise serializers.ValidationError(
                'Поле "tags" не может быть пустым'
            )
        self.exam_duplicate(data['tags'], 'tags')
        exam_duplicate_ingredients = [
            item.get('id') for item in data['ingredients']
        ]
        self.exam_duplicate(exam_duplicate_ingredients, 'ingredients')
        return data

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            RecipeTag.objects.create(recipe=recipe, tag=tag)
        for values in ingredients:
            RecipeIngredient.objects.create(
                ingredient=values['id'],
                recipe=recipe,
                amount=values['amount']
            )
        return recipe

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = self.context['request'].user
        recipe = int(representation['id'])

        tags = representation.pop('tags')
        tags_objects = []
        for tag in tags:
            tag_object = TagSerializers(Tag.objects.get(pk=tag))
            tags_objects += [tag_object.data]
        representation['tags'] = tags_objects

        author = RetrieveUserSerializer(instance=user)
        representation['author'] = author.data
        representation['is_favorited'] = self.already(user, recipe, Favorite)
        representation['is_in_shopping_cart'] = self.already(
            user, recipe, Shopping
        )
        for items in representation['ingredients']:
            pk = items.pop('id')
            ingredient = IngredientSerializers(
                instance=Ingredient.objects.get(id=pk)
            )
            items.update(ingredient.data)
        return representation

    def exam_duplicate(self, collection, f_string):
        if len(collection) != len(set(collection)):
            raise serializers.ValidationError(
                f'Поле {f_string} содержит повторяющиеся элементы'
            )

    def already(self, user, recipe, model):
        return model.objects.filter(user=user, recipe=recipe).exists()


class UpdateRecipeSerializer(CreateRecipeSerializer):
    image = Base64ImageField(required=False)

    def validate(self, data):
        if data.get('ingredients') is None:
            raise serializers.ValidationError(
                'Поле "ingredients" должно быть передано'
            )
        if data.get('tags') is None:
            raise serializers.ValidationError(
                'Поле "tags" должно быть передано'
            )
        return super().validate(data)

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text')
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.save()
        for tag in tags:
            RecipeTag.objects.get_or_create(recipe=instance, tag=tag)
        for values in ingredients:
            ingredient, *_ = RecipeIngredient.objects.get_or_create(
                ingredient=values['id'],
                recipe=instance
            )
            ingredient.amount = values['amount']
            ingredient.save()
        return instance


class GetRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializers(many=True)
    author = RetrieveUserSerializer()
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
        for ingredient in representation['ingredients']:
            ingredient['amount'] = RecipeIngredient.objects.get(
                recipe__id=instance.id,
                ingredient__id=int(ingredient['id'])).amount
        if self.context['request'].auth:
            user = self.context['request'].user
            representation['author'][
                'is_subscribed'
            ] = user.follower.filter(
                following__exact=int(representation['author']['id'])
            ).exists()
            representation["is_favorited"] = user.favourites.filter(
                recipe__exact=instance
            ).exists()
            representation["is_in_shopping_cart"] = user.shoppings.filter(
                recipe__exact=instance
            ).exists()
            return representation

        representation["is_favorited"] = False
        representation["is_in_shopping_cart"] = False
        return representation


class GetLinkSerializer(serializers.ModelSerializer):
    id = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='recipes-detail',
        lookup_url_kwarg='pk',
    )

    class Meta:
        model = Recipe
        fields = ('id', )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('id')
        return representation


class RecipeForListFollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'avatar',
        )
        read_only_fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'avatar',
        )

    def validate(self, data):
        if self.context.get("pk"):
            user = self.context['request'].user
            pk = self.context["pk"]
            following = get_object_or_404(User, pk=pk)
            if user.follower.filter(
                following__exact=following
            ).exists():
                raise serializers.ValidationError(
                    'Вы уже подписаны на этого пользователя'
                )
            if following == user:
                raise serializers.ValidationError(
                    'Нельзя подписаться на себя (даже если очень хочется).'
                )
            data['email'] = following.email
            data['id'] = following.id
            data['username'] = following.username
            data['first_name'] = following.first_name
            data['last_name'] = following.last_name
            data['avatar'] = following.avatar
        return data

    def create(self, validated_data):
        instance = Follow.objects.create(
            user=self.context['request'].user,
            following=User.objects.get(pk=self.context["pk"])
        )
        return instance

    def get_all_recipes(self, data):
        serializer = RecipeForListFollowSerializer(data, many=True)
        if self.context["recipes_limit"]:
            return serializer.data[:int(self.context["recipes_limit"])]
        return serializer.data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = self.context['request'].user
        following = User.objects.get(pk=int(representation['id']))
        representation['is_subscribed'] = user.follower.filter(
            following__exact=following
        ).exists()
        representation['recipes_count'] = following.recipes.count()
        representation['recipes'] = self.get_all_recipes(
            data=following.recipes.all()
        )
        return representation


class BaseFavoriteShoppingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['id', 'image', 'name', 'cooking_time']
        read_only_fields = ('id', 'image', 'name', 'cooking_time', )

    def validate(self, data):
        if self.context.get('pk'):
            recipe = get_object_or_404(Recipe, pk=self.context["pk"])
            data['id'] = recipe.id
            data['image'] = recipe.image
            data['name'] = recipe.name
            data['cooking_time'] = recipe.cooking_time
        return data


class FavoriteSerializer(BaseFavoriteShoppingSerializer):

    def validate(self, data):
        data = super().validate(data)
        if self.context.get('pk'):
            user = self.context['request'].user
            recipe = get_object_or_404(Recipe, pk=self.context["pk"])
            if user.favourites.filter(recipe__exact=recipe).exists():
                raise serializers.ValidationError(
                    'Вы уже добавили этот рецепт'
                )
        return data


class ShoppingSerializer(BaseFavoriteShoppingSerializer):

    def validate(self, data):
        data = super().validate(data)
        if self.context.get('pk'):
            user = self.context['request'].user
            recipe = get_object_or_404(Recipe, pk=self.context["pk"])
            if Shopping.objects.filter(user=user, recipe=recipe).exists():
                raise serializers.ValidationError(
                    'Вы уже добавили этот рецепт'
                )
        return data
