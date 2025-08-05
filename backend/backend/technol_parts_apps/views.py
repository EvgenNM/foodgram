from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response

import technol_parts_apps.serializers as s
from .models import Favorite, Ingredient, Recipe, Shopping, Tag
from .permissions import IsAuthorAuthenticated


class BaseTagIngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class TagViewSet(BaseTagIngredientViewSet):
    queryset = Tag.objects.all()
    serializer_class = s.TagSerializers


class Ingredient(BaseTagIngredientViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = s.IngredientSerializers
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Создание манипуляционного инструмента для рецепта"""
    http_method_names = ['post', 'get', 'patch', 'delete']
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author', )

    def get_queryset(self):
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )

        if self.request.query_params.get('tags'):
            tags_obj = Tag.objects.filter(
                slug__in=self.request.query_params.getlist('tags')
            )
            recipes_tags_queryset = Recipe.objects.filter(tags__in=tags_obj)

        if is_favorited and is_favorited.isdigit() and self.request.auth:
            filter_is_favorited = [
                item.recipe.id
                for item in self.request.user.favourites.all()
            ]
            if self.request.query_params.get('tags'):
                return recipes_tags_queryset.filter(
                    id__in=filter_is_favorited
                )[:int(is_favorited)]
            return Recipe.objects.filter(
                id__in=filter_is_favorited
            )[:int(is_favorited)]
        if (
            is_in_shopping_cart
            and is_in_shopping_cart.isdigit()
            and self.request.auth
        ):
            filter_is_in_shopping_cart = [
                item.recipe.id for
                item in self.request.user.shoppings.all()
            ]
            return Recipe.objects.filter(
                id__in=filter_is_in_shopping_cart
            )[:int(is_in_shopping_cart)]

        if self.request.query_params.get('tags'):
            return recipes_tags_queryset
        return Recipe.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return s.CreateRecipeSerializer
        if self.action == 'partial_update':
            return s.UpdateRecipeSerializer
        return s.GetRecipeSerializer

    def get_permissions(self):
        if self.action in (
            'doing_favorite', 'doing_shopping_cart', 'create',
        ):
            return (permissions.IsAuthenticated(), )
        if self.action in ('destroy', 'partial_update'):
            return (IsAuthorAuthenticated(), )
        return super().get_permissions()

    @action(
        detail=True,
        url_path='get-link',
        methods=['GET'],
    )
    def get_link(self, request, pk=None):

        if request.method in SAFE_METHODS:
            serializer = s.GetLinkSerializer(
                instance=self.get_object(),
                context={'request': request}
            )
            return Response(serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        url_path='favorite',
        methods=['POST', 'DELETE'],
    )
    def doing_favorite(self, request, pk=None):

        if request.method == 'POST':
            serializer = s.FavoriteSerializer(
                data=request.data,
                context={'request': request, 'pk': pk}
            )
            serializer.is_valid(raise_exception=True)
            Favorite.objects.create(
                user=self.request.user,
                recipe=Recipe.objects.get(pk=pk)
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            try:

                instance = Favorite.objects.get(
                    user=self.request.user,
                    recipe=recipe
                )
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ObjectDoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        url_path='shopping_cart',
        methods=['POST', 'DELETE'],

    )
    def doing_shopping_cart(self, request, pk=None):

        if request.method == 'POST':
            serializer = s.ShoppingSerializer(
                data=request.data,
                context={'request': request, 'pk': pk}
            )
            serializer.is_valid(raise_exception=True)
            Shopping.objects.create(
                user=self.request.user,
                recipe=Recipe.objects.get(pk=pk)
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, pk=pk)
            try:

                instance = Shopping.objects.get(
                    user=self.request.user,
                    recipe=recipe
                )
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ObjectDoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        url_path='download_shopping_cart',
        methods=['GET'],
    )
    def get_shopping_cart(self, request):

        if request.method in SAFE_METHODS:
            user_recipes_shopping_cart = [
                obj_shoppig.recipe.recipes_ingredient.all()
                for obj_shoppig in self.request.user.shoppings.all()
            ]
            shopping_cart = {}
            for ingrediets_values in user_recipes_shopping_cart:
                for ingredient_value in ingrediets_values:
                    shopping_cart[
                        ingredient_value.ingredient
                    ] = shopping_cart.get(
                        ingredient_value.ingredient, []
                    ) + [ingredient_value.amount]
            response = '\n'.join(
                [
                    f'{key.name}: {sum(value)} {key.measurement_unit}'
                    for key, value in shopping_cart.items()
                ]
            )

            filename = f"shopping_cart_{request.user.username}.txt"
            content = response
            response = HttpResponse(content, content_type='text/plain')
            response[
                'Content-Disposition'
            ] = f'attachment; filename={filename}'
            return response
