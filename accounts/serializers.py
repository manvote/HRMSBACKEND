# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User
from .models import Employee  # keep Employee serializer below





          



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
