from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import serializers

import users.constants as const
import base64
from technol_parts_apps.models import Follow
from django.core.files.base import ContentFile

import djoser.serializers as djs
User = get_user_model()

# ERROR_MESSAGES = {
#     'required': const.NOT_REQUIRED_MESSAGE,
#     'blank': const.NOT_BLANK_MESSAGE
# }


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='image.' + ext)

        return super().to_internal_value(data)


class AddAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar', )


class CreateTokenUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        password = attrs.get("password")
        params = {'email': attrs.get('email')}
        self.user = authenticate(
            request=self.context.get("request"),
            **params,
            password=password
        )
        if not self.user:
            self.user = User.objects.filter(**params).first()
            if self.user and not self.user.check_password(password):
                self.fail("invalid_credentials")
        if self.user and self.user.is_active:
            return attrs
        self.fail("invalid_credentials")


class CreateUserSerializer(djs.UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'username', 'email', 'password'
        )
        read_only_fields = ('id', )


class RetrieveUserSerializer(djs.UserSerializer):
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'username', 'email', 'avatar',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['is_subscribed'] = False
        return representation


class RetrieveOtherUserSerializer(RetrieveUserSerializer):

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context['request'].auth and representation.get('id'):
            representation['is_subscribed'] = Follow.objects.filter(
                user=self.context['request'].user,
                following=get_object_or_404(
                    User,
                    pk=representation['id'])).exists()
            return representation
        return representation
