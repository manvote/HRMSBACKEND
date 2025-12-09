from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from django.core.mail import send_mail
from django.conf import settings
from .serializers import SignupSerializer, LoginSerializer, OTPVerifySerializer

User = get_user_model()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
        "user_type": user.user_type,
        "email": user.email
    }

# ---------------- SIGNUP ----------------
class SignupView(GenericAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=SignupSerializer,
        responses={201: SignupSerializer},
        description="Register a new user (user, hr, admin)"
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = get_tokens_for_user(user)
        return Response({"user": serializer.data, "token": token}, status=status.HTTP_201_CREATED)


# ---------------- LOGIN (Send OTP) ----------------
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Login with email & password. If valid, OTP is sent to email."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
        )
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        otp = user.generate_otp()

        # Send OTP via email (prints to console in dev)
        send_mail(
            subject="HRMS Login OTP",
            message=f"Your OTP is {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"message": "OTP sent to email"}, status=status.HTTP_200_OK)


# ---------------- OTP VERIFY ----------------
class OTPVerifyView(GenericAPIView):
    serializer_class = OTPVerifySerializer
    permission_classes = [AllowAny]

    @extend_schema(
        request=OTPVerifySerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Verify OTP and receive JWT tokens"
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            user = User.objects.get(email=email, otp=otp)
        except User.DoesNotExist:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        user.otp = None
        user.save()

        token = get_tokens_for_user(user)
        return Response({"message": "Login successful", "token": token}, status=status.HTTP_200_OK)


# ---------------- CURRENT USER ----------------
class MeView(GenericAPIView):
    serializer_class = SignupSerializer

    @extend_schema(
        responses={200: SignupSerializer},
        description="Get currently logged-in user info (JWT required)"
    )
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
