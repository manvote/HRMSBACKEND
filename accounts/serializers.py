# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User
from .models import Employee  # keep Employee serializer below


# ====================================
# Authentication Serializers
# ====================================
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User email address")
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'},
        help_text="User password"
    )


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")
    first_login = serializers.BooleanField(help_text="Whether this is user's first login")
    redirect = serializers.CharField(help_text="Redirect path: 'reset-password' or 'dashboard'")


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        min_length=8,
        help_text="New password (minimum 8 characters)"
    )


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Response message")


# ====================================
# Employee Module Serializer
# ====================================
from rest_framework import serializers
from .models import Employee
from .models import EmployeeOffboarding, OffboardingChecklist,EmployeeDocument


class EmployeeSerializer(serializers.ModelSerializer):
    # INPUT: manager name
    reporting_manager = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Full name of reporting manager (e.g. Priya Sharma)"
    )

    # OUTPUT: manager name
    reporting_manager_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Employee
        fields = "__all__"

    # -------------------------
    # Helpers
    # -------------------------
    def get_reporting_manager_name(self, obj):
        if obj.reporting_manager:
            return f"{obj.reporting_manager.first_name} {obj.reporting_manager.last_name}".strip()
        return None

    def _find_manager(self, name):
        if not name:
            return None

        name = " ".join(name.split())
        parts = name.split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else None

        qs = Employee.objects.filter(first_name__iexact=first_name)
        if last_name:
            qs = qs.filter(last_name__iexact=last_name)

        return qs.first()

    # -------------------------
    # CREATE
    # -------------------------
    def create(self, validated_data):
        manager_name = validated_data.pop("reporting_manager", None)
        employee = Employee.objects.create(**validated_data)

        manager = self._find_manager(manager_name)
        if manager_name and not manager:
            raise serializers.ValidationError({
                "reporting_manager": "Reporting manager not found"
            })

        employee.reporting_manager = manager
        employee.save()
        return employee

    # -------------------------
    # UPDATE
    # -------------------------
    def update(self, instance, validated_data):
        manager_name = validated_data.pop("reporting_manager", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if manager_name is not None:
            manager = self._find_manager(manager_name)
            if manager_name and not manager:
                raise serializers.ValidationError({
                    "reporting_manager": "Reporting manager not found"
                })
            instance.reporting_manager = manager

        instance.save()
        return instance


# =================================================
# EMPLOYEE TAB SERIALIZERS
# =================================================

class EmployeeOverviewSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Employee
        fields = [
            "employee_code",
            "full_name",
            "date_of_birth",
            "gender",
            "email",
            "phone",
            "location",
            "date_of_joining",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["full_name"] = f"{instance.first_name} {instance.last_name}".strip()
        return data

    def update(self, instance, validated_data):
        full_name = validated_data.pop("full_name", None)

        if full_name:
            parts = full_name.strip().split(" ", 1)
            instance.first_name = parts[0]
            instance.last_name = parts[1] if len(parts) > 1 else ""

        return super().update(instance, validated_data)

class EmployeeJobSerializer(serializers.ModelSerializer):
    # 🔥 INPUT (STRING)
    reporting_manager_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Full name of reporting manager"
    )

    class Meta:
        model = Employee
        fields = [
            "department",
            "designation",
            "location",
            "employee_type",
            "work_shift",
            "work_timing",
            "probation_status",
            "reporting_manager_name",  # INPUT
        ]

    # 🔹 OUTPUT
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["reporting_manager_name"] = (
            f"{instance.reporting_manager.first_name} "
            f"{instance.reporting_manager.last_name}"
        ).strip() if instance.reporting_manager else None
        return data

    def update(self, instance, validated_data):
        manager_name = validated_data.pop("reporting_manager_name", None)

        # update normal fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if manager_name:
            name = " ".join(manager_name.split())
            parts = name.split(" ", 1)

            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else None

            qs = Employee.objects.filter(first_name__iexact=first_name)
            if last_name:
                qs = qs.filter(last_name__iexact=last_name)

            manager = qs.first()
            if not manager:
                raise serializers.ValidationError({
                    "reporting_manager_name": "Reporting manager not found"
                })

            instance.reporting_manager = manager

        instance.save()
        return instance


class EmployeeSalarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            "annual_ctc",
            "basic_pay",
            "allowances",
            "bonus",
        ]


# =================================================
# OFFBOARDING SERIALIZERS
# =================================================

class OffboardingChecklistSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(
        source="get_item_display",
        read_only=True
    )

    class Meta:
        model = OffboardingChecklist
        fields = ["id", "item", "display_name", "status"]


class EmployeeOffboardingSerializer(serializers.ModelSerializer):
    checklist = OffboardingChecklistSerializer(many=True, read_only=True)
    employee = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EmployeeOffboarding
        fields = [
            "id",
            "employee",
            "resignation_date",
            "last_working_date",
            "reason_for_exit",
            "additional_notes",
            "created_at",
            "checklist",
        ]
class EmployeeDocumentSerializer(serializers.ModelSerializer):
    # Return a safe URL for the file and size info without raising if file missing
    file = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDocument
        fields = [
            "id",
            "document_type",
            "file",
            "uploaded_at",
            "size",
        ]
        read_only_fields = ["uploaded_at"]

    def get_size(self, obj):
        try:
            if hasattr(obj, "file") and obj.file and hasattr(obj.file, "size"):
                return f"{obj.file.size / 1024:.2f} KB"
        except Exception:
            # In case storage backend raises when accessing size
            return None
        return None

    def get_file(self, obj):
        # Return a URL if possible, otherwise a filename or None.
        try:
            if hasattr(obj, "file") and obj.file:
                # obj.file.url may raise if file missing or storage misconfigured
                try:
                    return obj.file.url
                except Exception:
                    # Fall back to file name/path
                    try:
                        return obj.file.name
                    except Exception:
                        return None
        except Exception:
            return None
        return None

class EmployeeBulkActionSerializer(serializers.Serializer):
    employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of selected employee IDs"
    )
