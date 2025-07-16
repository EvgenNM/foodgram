from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns_v1 = [
    path('', include('users.urls')),
    path('', include('technol_parts_apps.urls')),
]


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(urlpatterns_v1))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)