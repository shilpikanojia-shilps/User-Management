from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('enroll.urls')),
    path("vendor/", include("vendor.urls", namespace="vendor")),
    path('vendor_api/', include('vendor_api.urls', namespace="vendor_api")),
    path('store/', include('store.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
