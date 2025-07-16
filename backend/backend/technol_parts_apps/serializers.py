from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework import serializers

import users.validators as vd
import users.constants as const
import base64
import time
import re

from django.core.files.base import ContentFile
from .models import Tag, Ingredient


User = get_user_model()


class TagSerializers(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializers(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'
