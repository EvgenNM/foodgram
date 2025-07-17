from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import serializers

import users.validators as vd
import users.constants as const
import base64
import time
import re

from django.core.files.base import ContentFile
from .models import Follow, Tag, Ingredient


User = get_user_model()


class TagSerializers(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


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
