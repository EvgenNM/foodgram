from django.urls import include, path

from rest_framework import routers

from .views import (
    TagViewSet,
    Ingredient,
    RecipeViewSet,
    FavoritesViewSet,
    CartViewSet

)

router = routers.DefaultRouter()
router.register('tags', TagViewSet, basename='genres')
router.register('ingredients', Ingredient, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('cart', CartViewSet, basename='cart')
router.register('favorites', FavoritesViewSet, basename='favorites')

urlpatterns = [
    path('', include(router.urls))
]
