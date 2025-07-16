from django.urls import include, path

from rest_framework import routers

from .views import (
    TagViewSet,
    Ingredient,
)

router = routers.DefaultRouter()
router.register('tags', TagViewSet, basename='genres')
router.register('ingredients', Ingredient, basename='ingredients')

urlpatterns = [
    path('', include(router.urls))
]