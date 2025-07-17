from django.urls import include, path

from rest_framework import routers

from .views import (
    FollowViewSet,
    TagViewSet,
    Ingredient,
)

router = routers.DefaultRouter()
router.register('tags', TagViewSet, basename='genres')
router.register('ingredients', Ingredient, basename='ingredients')
# router.register(
#     r'users/(?P<user_id>\d+)/subscribe',
#     FollowViewSet,
#     basename='followdoing'
# )

urlpatterns = [
    path('', include(router.urls))
]
