from rest_framework import filters, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import SAFE_METHODS
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import LimitOffsetPagination
# from .permissions import IsAdmin, IsUser
from .serializers import (
    User,
    UserCreateSerializer,
    UserProfileSerializer,
    ChangePasswordSerializers,
    CreateTokenSerializer,
    AddAvatarSerializer,

)
from technol_parts_apps.models import Follow, Favorite, Recipe
from technol_parts_apps.serializers import FollowSerializer, FollowListSerializer, FavoriteSerializer
from django.shortcuts import get_object_or_404

import djoser.views
from django_filters.rest_framework import DjangoFilterBackend

class AddAvatarView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = AddAvatarSerializer(
            instance=request.user,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenCreateView(APIView):
    """Получение токена."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CreateTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(
            email=serializer.data['email'],
            )

        # ручное создание токена
        refresh = RefreshToken.for_user(user)
        data = {
            'auth_token': str(refresh.access_token),
        }
        return Response(data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializers(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response('Пароль изменен', status=status.HTTP_204_NO_CONTENT)


class Logout(APIView):

    def post(self, request):
        if request.user.is_authenticated:
            token_access = RefreshToken(request.data.get('access'))
            token_refresh = RefreshToken(request.data.get('refresh'))
            token_access.blacklist()
            token_refresh.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        data = {'detail': 'Учетные данные не были предоставлены.'}
        return Response(data, status=status.HTTP_401_UNAUTHORIZED)


class CreateUserProfilelistViewSet(viewsets.ModelViewSet):
    """Создание манипуляционного инструмента пользователями для админа."""
    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'delete']
    # filter_backends = (filters.SearchFilter,)
    pagination_class = LimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserProfileSerializer

    def get_permissions(self):
        if self.action in (
            'get_user_self', 'doing_subscribe', 'list_subscribe'
        ):
            return (permissions.IsAuthenticated(),)
        # if self.action == 'list':
        #     return (permissions.IsAdminUser(), )
        return (permissions.AllowAny(), )

    # Исключить удаление пользователя!!!!!!!!!!!!!!!

    @action(
        detail=False,
        url_path='me',
        methods=['GET'],
    )
    def get_user_self(self, request):

        if request.method in SAFE_METHODS:
            serializer = UserProfileSerializer(self.request.user)
            return Response(serializer.data)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
            detail=True,
            url_path='subscribe',
            methods=['POST', 'DELETE'],
    )
    def doing_subscribe(self, request, pk=None):

        def get_data_context_serializer():
            return FollowSerializer(
                data=request.data,
                context={'request': request, 'pk': pk}
            )

        if request.method == 'POST':
            serializer = get_data_context_serializer()
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(
                user=self.request.user,
                following=get_object_or_404(User, pk=pk)
            )
            return Response(serializer.data)

        if request.method == 'DELETE':
            # serializer = get_data_context_serializer()
            # serializer.is_valid()
            instance = get_object_or_404(
                Follow,
                user=self.request.user,
                following=pk
                # following=serializer.data['following']
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
            detail=False,
            url_path='subscriptions',
            methods=['GET'],
    )
    def list_subscribe(self, request):
        if request.method in SAFE_METHODS:
            serializer = FollowListSerializer(
                data=request.user.follower.all(), many=True
            )
            serializer.is_valid()
            return Response(serializer.data)
        

######################################
# РАБОТА с ДЖОСЕРОМ ##################
######################################


class UserrsViwset(djoser.views.UserViewSet):
    pagination_class = LimitOffsetPagination
    lookup_field = 'pk'

    def get_queryset(self):
        return User.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (permissions.AllowAny(), )
        if self.action in ('doing_subscribe', 'list_subscribe'):
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        if self.action != 'me':
            instance = get_object_or_404(User, pk=kwargs['pk'])
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return super().retrieve(request, *args, **kwargs)

    @action(
            detail=True,
            url_path='subscribe',
            methods=['POST', 'DELETE'],
    )
    def doing_subscribe(self, request, pk=None):

        def get_data_context_serializer():
            return FollowSerializer(
                data=request.data,
                context={'request': request, 'pk': pk}
            )

        if request.method == 'POST':
            serializer = get_data_context_serializer()
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(
                user=self.request.user,
                following=get_object_or_404(User, pk=pk)
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            instance = get_object_or_404(
                Follow,
                user=self.request.user,
                following=pk
            )
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
            detail=False,
            url_path='subscriptions',
            methods=['GET'],
            pagination_class=LimitOffsetPagination
    )
    def list_subscribe(self, request):
        if request.method in SAFE_METHODS:
            serializer = FollowListSerializer(
                data=request.user.follower.all(), many=True
            )
            serializer.is_valid()
            return Response(serializer.data)
