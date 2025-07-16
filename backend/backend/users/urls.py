from django.urls import include, path

from rest_framework import routers

from .views import (
    CreateUserProfilelistViewSet,
    Logout,
    ChangePasswordView,
    TokenCreateView,
    AddAvatarView,
)


router = routers.DefaultRouter()
router.register('', CreateUserProfilelistViewSet)


urlpatterns_users = [
    path(
        'set_password/',
        ChangePasswordView.as_view(),
        name='change_password'
    ),
    path('me/avatar/', AddAvatarView.as_view(), name='do_avatar'),
    path('', include(router.urls)),
]

urlpatterns_auth_token = [
    path(
        'login/',
        TokenCreateView.as_view(),
        name='token_create'
    ),
    path('logout/', Logout.as_view(), name='logout'),
]

urlpatterns = [
    path('users/', include(urlpatterns_users)),
    path('auth/token/', include(urlpatterns_auth_token)),
]
