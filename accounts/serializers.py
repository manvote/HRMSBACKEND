# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User
from .models import Employee  # keep Employee serializer below


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "user_type"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        # create user with must_change_password default (True) unless specified
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password")

        return {
            "user_id": user.id,
            "email": user.email,
            "user_type": user.user_type,
            "must_change_password": getattr(user, "must_change_password", False),
            "message": "Login successful"
        }


class ChangePasswordSerializer(serializers.Serializer):
    """
    Used for authenticated users to change their password.
    Requires: old_password, new_password, new_password_confirm
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        # run standard Django validators
        validate_password(value)
        return value

    def validate(self, attrs):
        # new passwords match
        if attrs.get("new_password") != attrs.get("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})

        request = self.context.get("request")
        user = None
        if request and hasattr(request, "user"):
            user = request.user

        # For authenticated users, check old password
        if user and user.is_authenticated:
            if not user.check_password(attrs["old_password"]):
                raise serializers.ValidationError({"old_password": "Incorrect old password"})
        else:
            # Not authenticated: we do not support unauthenticated change in this serializer
            raise serializers.ValidationError("Authentication required to change password.")

        return attrs

    def save(self, **kwargs):
        request = self.context.get("request")
        user = request.user
        user.set_password(self.validated_data["new_password"])
        # clear first-time-change flag
        if hasattr(user, "must_change_password"):
            user.must_change_password = False
        user.save()
        return user


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "user_type"]


# ====================================
# Employee Module Serializer
# ====================================
class EmployeeSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(
        required=False,
        allow_null=True,
        use_url=True
    )

    class Meta:
        model = Employee
        fields = "__all__"
