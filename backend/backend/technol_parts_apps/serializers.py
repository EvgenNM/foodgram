import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

import technol_parts_apps.constants as const
import technol_parts_apps.models as md
import technol_parts_apps.validators as vd
from users.serializers import RetrieveUserSerializer

User = get_user_model()


class TagSerializers(serializers.ModelSerializer):

    class Meta:
        model = md.Tag
        fields = ('id', 'name', 'slug', )
        read_only_fields = ('name', 'slug', )


class IngredientSerializers(serializers.ModelSerializer):

    class Meta:
        model = md.Ingredient
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
        queryset=md.Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        validators=vd.amount_validators,
        write_only=True
    )

    class Meta:
        model = md.Ingredient
        fields = ('id', 'amount', )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        id = representation.pop('id')
        ingredient = md.Ingredient.objects.get(id=id)
        ingredient_serializer = IngredientSerializers(instance=ingredient)
        representation.update(ingredient_serializer.data)
        representation['amount'] = instance.ingredient_recipes.last().amount
        return representation


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    name = serializers.CharField(
        max_length=const.RECIPE_NAME_LENGTH,
    )
    cooking_time = serializers.IntegerField(
        validators=vd.cooking_time_validators
    )
    text = serializers.CharField(
        source='description',
        max_length=const.TEXT_LENGTH,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=md.Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeIngredientSerializer(many=True)

    class Meta:
        model = md.Recipe
        fields = [
            'id', 'image', 'name', 'text', 'cooking_time',
            'tags', 'ingredients', 'author'
        ]
        read_only_fields = ('id', 'author', 'image',)

    def validate(self, data):
        if data.get('ingredients') is None:
            raise serializers.ValidationError(
                'Поле "ingredients" должно быть передано'
            )
        if data.get('tags') is None:
            raise serializers.ValidationError(
                'Поле "tags" должно быть передано'
            )
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
        recipe = md.Recipe.objects.create(**validated_data)
        md.RecipeTag.objects.bulk_create(
            self.tags_recipes_objects(tags, recipe)
        )
        recipe_ingredient_objects = [
            md.RecipeIngredient(
                ingredient=values['id'],
                recipe=recipe,
                amount=values['amount']
            )
            for values in ingredients
        ]
        md.RecipeIngredient.objects.bulk_create(recipe_ingredient_objects)
        return recipe

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
        instance.tags.set(tags)
        for values in ingredients:
            ingredient, *_ = md.RecipeIngredient.objects.get_or_create(
                ingredient=values['id'],
                recipe=instance,
            )
            ingredient.amount = values['amount']
            ingredient.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = self.context['request'].user
        recipe = int(representation['id'])

        tags = representation.pop('tags')
        tags_objects = md.Tag.objects.filter(id__in=tags)
        tags_objects_serializer = TagSerializers(tags_objects, many=True)
        representation['tags'] = tags_objects_serializer.data

        author = RetrieveUserSerializer(instance=user)
        representation['author'] = author.data
        representation['is_favorited'] = self.already(
            user, recipe, md.Favorite
        )
        representation['is_in_shopping_cart'] = self.already(
            user, recipe, md.Shopping
        )
        return representation

    def exam_duplicate(self, collection, f_string):
        if len(collection) != len(set(collection)):
            raise serializers.ValidationError(
                f'Поле {f_string} содержит повторяющиеся элементы'
            )

    def already(self, user, recipe, model):
        return model.objects.filter(user=user, recipe=recipe).exists()

    def tags_recipes_objects(self, list_tags, recipe):
        tag_recipes_objects = [
            md.RecipeTag(recipe=recipe, tag=tag)
            for tag in list_tags
        ]
        return tag_recipes_objects


class GetRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializers(many=True)
    author = RetrieveUserSerializer()
    ingredients = IngredientSerializers(many=True)
    text = serializers.CharField(source='description')

    class Meta:
        model = md.Recipe
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
            ingredient['amount'] = md.RecipeIngredient.objects.get(
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
        model = md.Recipe
        fields = ('id', )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = representation.pop('id')
        return representation


class RecipeForListFollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = md.Recipe
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
        instance = md.Follow.objects.create(
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


class BaseFavoriteShoppingSerializer(serializers.Serializer):

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context.get('pk'):
            recipe = get_object_or_404(md.Recipe, pk=self.context["pk"])
            recipe_serializer = RecipeForListFollowSerializer(recipe)
            representation.update(recipe_serializer.data)
        return representation


class FavoriteSerializer(BaseFavoriteShoppingSerializer):

    def validate(self, data):
        data = super().validate(data)
        if self.context.get('pk'):
            user = self.context['request'].user
            recipe = get_object_or_404(md.Recipe, pk=self.context["pk"])
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
            recipe = get_object_or_404(md.Recipe, pk=self.context["pk"])
            if user.shoppings.filter(recipe__exact=recipe).exists():
                raise serializers.ValidationError(
                    'Вы уже добавили этот рецепт'
                )
        return data
