from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import serializers

import users.validators as vd
import users.constants as const
import base64
import time
import re
from technol_parts_apps.models import Follow
from django.core.files.base import ContentFile

from djoser.serializers import (
    UserSerializer, UserCreateSerializer, SetPasswordSerializer,
    TokenSerializer, TokenCreateSerializer
)

import djoser.serializers as djs
User = get_user_model()

ERROR_MESSAGES = {
    'required': const.NOT_REQUIRED_MESSAGE,
    'blank': const.NOT_BLANK_MESSAGE
}


class FieldsUsernamePasswordSerializers(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        max_length=const.EMAIL_FIELD_LENGTH,
        error_messages=ERROR_MESSAGES,
    )
    password = serializers.CharField(
        max_length=const.PASSWORD_LENGTH,
        required=True,
        error_messages=ERROR_MESSAGES,
    )


class CreateTokenSerializer(FieldsUsernamePasswordSerializers):

    class Meta:
        model = User
        fields = ('email', 'password')

    def validate(self, data):
        if not User.objects.filter(
            email=data['email'],
            password=data['password']
        ).exists():
            raise serializers.ValidationError(
                'Пользователя с таким паролем или email нет'
            )
        return data


class ChangePasswordSerializers(serializers.ModelSerializer):
    new_password = serializers.CharField(
        max_length=const.PASSWORD_LENGTH,
        required=True,
        error_messages=ERROR_MESSAGES,
        validators=[vd.validator_password]
    )
    current_password = serializers.CharField(
        max_length=const.PASSWORD_LENGTH,
        required=True,
        error_messages=ERROR_MESSAGES,
        source='password'
    )

    class Meta:
        model = User
        fields = ('new_password', 'current_password')

    def validate(self, data):
        if data['new_password'] == data['password']:
            raise serializers.ValidationError(
                'Нельзя заменить пароль на такой же'
            )
        if data['password'] != self.context['request'].user.password:
            raise serializers.ValidationError(
                'Неправильно введен действующий пароль'
            )
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        user.password = validated_data['new_password']
        user.save()
        return user


class AbstractUserSerializer(FieldsUsernamePasswordSerializers):
    """Сериализатор. Поля для работы с моделью пользователя."""
    first_name = serializers.CharField(
        max_length=const.FIRST_NAME_LENGTH,
        required=True,
        error_messages=ERROR_MESSAGES
    )
    last_name = serializers.CharField(
        max_length=const.LAST_NAME_LENGTH,
        required=True,
        error_messages=ERROR_MESSAGES
    )
    username = serializers.CharField(
        max_length=const.USERNAME_LENGTH,
        required=True,
        validators=[
            vd.re_validator_username,
            vd.validator_username_on_me
        ],
        error_messages=ERROR_MESSAGES
        )
    password = serializers.CharField(
        max_length=const.PASSWORD_LENGTH,
        required=True,
        error_messages=ERROR_MESSAGES,
        validators=[vd.validator_password]
    )


class UserCreateSerializer(AbstractUserSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'username', 'email', 'password'
        )
        read_only_fields = ('id', )

    def validate(self, data):
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError(
                'Данный никнейм уже занят'
            )
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                'Данный email не подходит. Введите другой email'
            )
        vd.exam_password(data)
        data['first_name'] = data['first_name'].title()
        data['last_name'] = data['last_name'].title()
        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('password')
        return representation

class UserProfileSerializer(AbstractUserSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name',
            'username', 'email', 'avatar',
        )


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


##########################################################
#    СЕРИАЛИЗАТОРЫ ДЖОСЕРА !!!!!!!!!!!!!!!!!!!!!!!!!!    #
##########################################################

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
    is_subscribed = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'username',
            'email', 'avatar', 'is_subscribed'
        )
        read_only_fields = ('id', 'is_subscribed')

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


# class ResetPasswordSerializer(djs.SetPasswordSerializer):

#     def validate(self, attrs):
#         user = self.context["request"].user or self.user
#         # why assert? There are ValidationError / fail everywhere
#         assert user is not None

#         try:
#             validate_password(attrs["new_password"], user)
#         except django_exceptions.ValidationError as e:
#             raise serializers.ValidationError({"new_password": list(e.messages)})
#         return super().validate(attrs)
