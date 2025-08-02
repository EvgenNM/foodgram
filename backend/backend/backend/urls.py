from django.contrib import admin
from django.urls import include, path

urlpatterns_v1 = [
    path('', include('technol_parts_apps.urls')),
    path('', include('users.urls')),
]


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(urlpatterns_v1))
]
