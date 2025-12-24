from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


# ==========================
# CUSTOM USER MANAGER
# ==========================
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


# ==========================
# CUSTOM USER MODEL
# ==========================
class User(AbstractUser):
    username = None  # ❌ remove username
    email = models.EmailField(unique=True)

    is_super_admin = models.BooleanField(default=False)
    first_login = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()  # ✅ THIS LINE FIXES createsuperuser


# ==========================
# EMPLOYEE MODEL
# ==========================
# ==========================
# EMPLOYEE MODEL (SANThOSH)
# ==========================
from django.db import models


class Employee(models.Model):

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("ON_LEAVE", "On Leave"),
        ("INACTIVE", "Inactive"),
    ]

    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    ]
    

    EMPLOYEE_TYPE_CHOICES = (
        ("FULL_TIME", "Full Time"),
        ("TEMPORARY", "Temporary"),
    )

    PROBATION_STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
    )

    SHIFT_CHOICES = (
        ("DAY", "Day Shift"),
        ("NIGHT", "Night Shift"),
        ("ROTATIONAL", "Rotational Shift"),
    )

    employee_code = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    phone = models.CharField(max_length=15, null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)

    photo = models.ImageField(
        upload_to="employees/photos/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
     # 🔥 NEW HR FIELDS
    reporting_manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reportees"
    )

    employee_type = models.CharField(
        max_length=20,
        choices=EMPLOYEE_TYPE_CHOICES,
        default="FULL_TIME"
    )

    work_shift = models.CharField(
        max_length=20,
        choices=SHIFT_CHOICES,
        default="DAY"
    )

    work_timing = models.CharField(
        max_length=50,
        default="09:00 AM - 06:00 PM"
    )

    probation_status = models.CharField(
        max_length=20,
        choices=PROBATION_STATUS_CHOICES,
        default="PENDING"
    )

    # 💰 SALARY
    annual_ctc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    basic_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.employee_code
# ============================
# EMPLOYEE OFFBOARDING
# ============================

class EmployeeOffboarding(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="offboarding"
    )
    resignation_date = models.DateField()
    last_working_date = models.DateField()
    reason_for_exit = models.CharField(max_length=255)
    additional_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offboarding - {self.employee.employee_code}"


# ============================
# OFFBOARDING CHECKLIST
# ============================

class OffboardingChecklist(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUBMITTED", "Submitted"),
    ]

    CHECKLIST_CHOICES = [
        ("LAPTOP_RETURNED", "Laptop Returned"),
        ("ACCESS_CARD", "Access Card Returned"),
        ("DOCUMENTS", "Documents Submitted"),
        ("NO_DUES", "No Dues Clearance"),
        ("KNOWLEDGE_TRANSFER", "Knowledge Transfer Completed"),
    ]

    offboarding = models.ForeignKey(
        EmployeeOffboarding,
        on_delete=models.CASCADE,
        related_name="checklist"
    )

    item = models.CharField(max_length=50, choices=CHECKLIST_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    def __str__(self):
        return f"{self.item} - {self.status}"


class EmployeeDocument(models.Model):
    DOCUMENT_TYPES = (
        ("RESUME", "Resume"),
        ("ID_PROOF", "ID Proof"),
        ("OFFER_LETTER", "Offer Letter"),
        ("EXPERIENCE", "Experience Letter"),
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to="employee_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("employee", "document_type")

    def __str__(self):
        return f"{self.employee_id} - {self.document_type}"
