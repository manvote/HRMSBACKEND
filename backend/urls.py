from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # All authentication + employee module APIs
    path("api/", include("accounts.urls")),   # signup + employee routes together

    # API schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    # Redoc documentation
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
