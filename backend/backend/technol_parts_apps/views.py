from django.shortcuts import get_object_or_404
from django.http import FileResponse
from rest_framework import filters, permissions, viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import SAFE_METHODS
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
# from .permissions import IsAdmin, IsUser
from .models import Tag, Ingredient, Recipe, Favorite, Shopping
from rest_framework import filters
from .serializers import (
    User,
    FollowSerializer,
    TagSerializers,
    IngredientSerializers,
    CreateRecipeSerializer,
    GetRetrieveRecipeSerializer,
    UpdateRecipeSerializer,
    GetLinkSerializer,
    FavoriteSerializer,
    ShoppingSerializer,
    listRecipeSerializer
)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (permissions.AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializers
    pagination_class = None


class Ingredient(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (permissions.AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializers
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Создание манипуляционного инструмента для рецепта"""
    queryset = Recipe.objects.all()
    http_method_names = ['post', 'get', 'patch', 'delete']
    # permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author', 'tags')

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateRecipeSerializer
        if self.action == 'partial_update':
            return UpdateRecipeSerializer
        if self.action == 'list':
            return listRecipeSerializer
        return GetRetrieveRecipeSerializer
    
    def get_permissions(self):
        if self.action in ('doing_favorite', 'doing_shopping_cart'):
            return (permissions.IsAuthenticated(), )
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        if not request.auth:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        if not request.auth:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return super().retrieve(request, *args, **kwargs)

    @action(
            detail=True,
            url_path='get-link',
            methods=['GET'],
    )
    def get_link(self, request, pk=None):

        if request.method in SAFE_METHODS:
            serializer = GetLinkSerializer(
                instance=self.get_object(),
                context={'request': request}
            )
            return Response(serializer.data)

    @action(
            detail=True,
            url_path='favorite',
            methods=['POST', 'DELETE'],
    )
    def doing_favorite(self, request, pk=None):

        if request.method == 'POST':
            serializer = FavoriteSerializer(
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
            instance = get_object_or_404(
                Favorite,
                user=self.request.user,
                recipe=pk
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
            detail=True,
            url_path='shopping_cart',
            methods=['POST', 'DELETE'],
    )
    def doing_shopping_cart(self, request, pk=None):

        if request.method == 'POST':
            serializer = ShoppingSerializer(
                data=request.data,
                context={'request': request, 'pk': pk}
            )
            serializer.is_valid(raise_exception=True)
            Shopping.objects.create(
                user=self.request.user,
                recipe=Recipe.objects.get(pk=pk)
            )
            return Response(status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            instance = get_object_or_404(
                Shopping,
                user=self.request.user,
                recipe=pk
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

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
                        ingredient_value.ingredient.name
                    ] = shopping_cart.get(
                        ingredient_value.ingredient.name, []
                    ) + [ingredient_value.amount]
            response = '\n'.join(
                [
                    f'{key}: {sum(value)}'
                    for key, value in shopping_cart.items()
                ]
            )

            # with open('shopping_cart.txt', 'w', encoding='utf-8') as carts:
            #     print(response, file=carts)
            #     return FileResponse(carts)

            return Response(response)


class FollowViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.follower.all()

    # def get_user_follow(self):
    #     user_id = self.kwargs['user_id']
    #     return get_object_or_404(User, pk=user_id)

    # def perform_create(self, serializer):
    #     serializer.save(
    #         user=self.request.user,
    #         following=self.get_user_follow()
    #     )

    # def perform_destroy(self, instance):
    #     instance = self.request.user.follower.filter(
    #         following__exact=self.get_user_follow()
    #     )
    #     instance.delete()
