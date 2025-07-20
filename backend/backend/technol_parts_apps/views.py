from django.shortcuts import get_object_or_404

from rest_framework import filters, permissions, viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import SAFE_METHODS

from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken

# from .permissions import IsAdmin, IsUser
from .models import Tag, Ingredient, Recipe
from .serializers import (
    User,
    FollowSerializer,
    TagSerializers,
    IngredientSerializers,
    CreateRecipeSerializer,
    GetRetrieveRecipeSerializer,
    UpdateRecipeSerializer,
    GetLinkSerializer
)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (permissions.AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializers


class Ingredient(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = (permissions.AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializers
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Создание манипуляционного инструмента для рецепта"""
    queryset = Recipe.objects.all()
    http_method_names = ['post', 'get', 'patch', 'delete']
    # permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateRecipeSerializer
        if self.action == 'partial_update':
            return UpdateRecipeSerializer
        return GetRetrieveRecipeSerializer

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
