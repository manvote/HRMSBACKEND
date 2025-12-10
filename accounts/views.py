from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    MeSerializer,
)
from .models import User


# REGISTER
@extend_schema(
    tags=["Auth"],
    request=RegisterSerializer,
    responses={201: dict},
    description="Register new HRMS user"
)
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=201)
        return Response(serializer.errors, status=400)


# LOGIN
@extend_schema(
    tags=["Auth"],
    request=LoginSerializer,
    responses={200: dict},
    description="Login using email + password to get JWT tokens"
)
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(id=serializer.validated_data["user_id"])

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": serializer.validated_data
        }, status=200)


# CHANGE PASSWORD
@extend_schema(
    tags=["Auth"],
    request=ChangePasswordSerializer,
    responses={200: dict},
    description="Update password of logged-in user"
)
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password updated successfully"}, status=200)


# WHO IS LOGGED IN
@extend_schema(
    tags=["Auth"],
    responses=MeSerializer,
    description="Get details of currently authenticated user"
)
class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)
