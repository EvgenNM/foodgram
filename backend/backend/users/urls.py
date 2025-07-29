from django.urls import include, path

from rest_framework import routers

from .views import (
    AddAvatarView,
    UserrsViwset,
)

import djoser.views


router = routers.DefaultRouter()
router.register('', UserrsViwset)


urlpatterns_users = [
    path('me/avatar/', AddAvatarView.as_view(), name='do_avatar'),
    path('', include(router.urls)),
]

urlpatterns_auth_token = [
    path(
        'login/',
        djoser.views.TokenCreateView.as_view(),
        name='token_create'
    ),
    path('logout/', djoser.views.TokenDestroyView.as_view(), name='logout'),
]

urlpatterns = [
    path('users/', include(urlpatterns_users)),
    path('auth/token/', include(urlpatterns_auth_token)),
]
