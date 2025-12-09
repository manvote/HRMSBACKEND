from django.urls import path
from .views import SignupView, LoginView, OTPVerifyView, MeView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("otp-verify/", OTPVerifyView.as_view(), name="otp-verify"),
    path("me/", MeView.as_view(), name="me"),
]
