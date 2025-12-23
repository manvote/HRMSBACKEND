from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # ❌ Remove username completely
    username = None

    # ✅ Use email as login
    email = models.EmailField(unique=True)

    is_super_admin = models.BooleanField(default=False)
    first_login = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


# ==========================
# EMPLOYEE MODEL (SANThOSH)
# ==========================
class Employee(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("ON_LEAVE", "On Leave"),
        ("INACTIVE", "Inactive"),
    ]

    employee_code = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    phone = models.CharField(max_length=15, null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)

    # ✅ ADD THIS
    photo = models.ImageField(
        upload_to="employees/photos/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
