from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import random

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, user_type="user"):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), user_type=user_type)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email=email, password=password, user_type="admin")
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ("user", "User"),
        ("hr", "HR"),
        ("admin", "Admin"),
    )

    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default="user")
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, blank=True, null=True)  # OTP for login verification

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.save()
        return self.otp
