from django.urls import include, path

from rest_framework import routers

from .views import (
    FollowViewSet,
    TagViewSet,
    Ingredient,
    RecipeViewSet
)

router = routers.DefaultRouter()
router.register('tags', TagViewSet, basename='genres')
router.register('ingredients', Ingredient, basename='ingredients')
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls))
]
