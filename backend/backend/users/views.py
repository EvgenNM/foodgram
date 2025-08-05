import djoser.views
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from technol_parts_apps.models import Follow
from technol_parts_apps.serializers import FollowSerializer
from .serializers import AddAvatarSerializer, User


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
                context={
                    'request': request,
                    'pk': pk,
                    'recipes_limit': self.request.query_params.get(
                        'recipes_limit'
                    )
                }
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
            following = get_object_or_404(User, pk=pk)
            try:
                instance = Follow.objects.get(
                    user=self.request.user,
                    following=following
                )
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ObjectDoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        url_path='subscriptions',
        methods=['GET'],
        pagination_class=LimitOffsetPagination
    )
    def list_subscribe(self, request):
        subscriptions = User.objects.filter(id__in=[
            item.following.id for item in request.user.follower.all()
        ])
        if self.paginator is not None:
            page = self.paginate_queryset(subscriptions)
            serializer = FollowSerializer(
                page,
                many=True,
                context={
                    'request': request,
                    'recipes_limit': self.request.query_params.get(
                        'recipes_limit'
                    )
                },

            )
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(subscriptions, many=True)
        return Response(serializer.data)
