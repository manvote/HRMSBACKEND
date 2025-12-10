from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("accounts.urls")),

    # Swagger + Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="api-schema")),
]
