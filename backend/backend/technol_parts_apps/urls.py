import technol_parts_apps.views as vi
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register('tags', vi.TagViewSet, basename='genres')
router.register('ingredients', vi.Ingredient, basename='ingredients')
router.register('recipes', vi.RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls))
]
