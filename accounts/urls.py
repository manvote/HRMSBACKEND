from django.urls import path,include
from .views import RegisterView, LoginView, ChangePasswordView, MeView
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet
# ----------------------------
# Router for Employee module
# ----------------------------
router = DefaultRouter()
router.register(r"employees", EmployeeViewSet, basename="employee")
urlpatterns = [
   # path("register/", RegisterView.as_view()),#
    path("login/", LoginView.as_view()),
    path("change-password/", ChangePasswordView.as_view()),
    path("me/", MeView.as_view()),
     # Employee module URLs
    path("", include(router.urls)),
]
