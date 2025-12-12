# accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    MeSerializer,
)
from .models import User

# Register
@extend_schema(
    tags=["Auth"],
    request=RegisterSerializer,
    responses={201: dict},
    description="Register new HRMS user"
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User registered successfully"}, status=201)


# Login
@extend_schema(
    tags=["Auth"],
    request=LoginSerializer,
    responses={200: dict},
    description="Login using email + password to get JWT tokens"
)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(id=serializer.validated_data["user_id"])

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": serializer.validated_data,
            # include must_change_password so frontend can redirect to change-password flow
            "must_change_password": getattr(user, "must_change_password", False)
        }, status=200)


# Change Password
@extend_schema(
    tags=["Auth"],
    request=ChangePasswordSerializer,
    responses={200: dict},
    description="Update password of logged-in user"
)
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # After success, it's recommended to force user to login again on frontend
        return Response({"message": "Password updated successfully"}, status=200)


# Who is logged in
@extend_schema(
    tags=["Auth"],
    responses=MeSerializer,
    description="Get details of currently authenticated user"
)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)



# ============================================================
# Employee Module 
# ============================================================

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from django.db.models import Q, Count
from .models import Employee
from .serializers import EmployeeSerializer
import csv, io
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema


    # FILTERING (search, department, status, location)
class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Employee.objects.all().order_by("employee_code")
    serializer_class = EmployeeSerializer

    def get_permissions(self):
        if self.action == "list" and self.request.query_params:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        qs = Employee.objects.all()
        params = self.request.query_params

        search = params.get("search") or params.get("query")
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(employee_code__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        department = params.get("department")
        status_param = params.get("status")
        location = params.get("location")

        if department:
            qs = qs.filter(department__iexact=department)
        if status_param:
            qs = qs.filter(status__iexact=status_param)
        if location:
            qs = qs.filter(location__iexact=location)

        sort = params.get("sort")
        if sort == "name_asc":
            qs = qs.order_by("first_name")
        elif sort == "name_desc":
            qs = qs.order_by("-first_name")
        elif sort == "code_asc":
            qs = qs.order_by("employee_code")
        elif sort == "code_desc":
            qs = qs.order_by("-employee_code")

        return qs

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        qs = Employee.objects.all()
        return Response({
            "total_employees": qs.count(),
            "active": qs.filter(status="ACTIVE").count(),
            "on_leave": qs.filter(status="ON_LEAVE").count(),
            "department_breakdown": list(
                qs.values("department").annotate(count=Count("id"))
            ),
        })

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                },
                "required": ["file"]
            }
        },
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=["post"], url_path="bulk-upload",
            parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        ...
        return Response({"created": created, "updated": updated, "errors": errors})

    @action(detail=False, methods=["get"], url_path="export")
    def export_employees(self, request):
        ...
        return response


    # ---------------- EMPLOYEE STATS ----------------
    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        qs = Employee.objects.all()
        data = {
            "total_employees": qs.count(),
            "active": qs.filter(status="ACTIVE").count(),
            "on_leave": qs.filter(status="ON_LEAVE").count(),
            "department_breakdown": list(
                qs.values("department").annotate(count=Count("id"))
            ),
        }
        return Response(data)

    # ---------------- BULK UPLOAD CSV ----------------
    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "Upload CSV file"
                    }
                },
                "required": ["file"]
            }
        },
        responses={200: OpenApiTypes.OBJECT},
        description="Bulk upload employees using CSV file"
    )
    @action(detail=False, methods=["post"], url_path="bulk-upload",
            parser_classes=[MultiPartParser, FormParser])
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        try:
            decoded = file.read().decode("utf-8")
        except:
            return Response({"error": "File must be UTF-8 encoded CSV"}, status=400)

        reader = csv.DictReader(io.StringIO(decoded))
        created, updated, errors = 0, 0, []

        for idx, row in enumerate(reader, start=1):
            try:
                emp, is_created = Employee.objects.update_or_create(
                    employee_code=row.get("employee_code"),
                    defaults={
                        "first_name": row.get("first_name"),
                        "last_name": row.get("last_name"),
                        "email": row.get("email"),
                        "department": row.get("department"),
                        "designation": row.get("designation"),
                        "location": row.get("location"),
                        "phone": row.get("phone"),
                        "date_of_joining": row.get("date_of_joining"),
                        "status": row.get("status", "ACTIVE"),
                    }
                )
                created += int(is_created)
                updated += int(not is_created)
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")

        return Response({"created": created, "updated": updated, "errors": errors})

    # ---------------- EXPORT EMPLOYEES ----------------
    @action(detail=False, methods=["get"], url_path="export")
    def export_employees(self, request):
        from django.http import HttpResponse
        import csv

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=employees.csv"

        writer = csv.writer(response)
        writer.writerow([
            "employee_code", "first_name", "last_name", "email",
            "department", "designation", "location", "phone",
            "date_of_joining", "status", "created_at", "updated_at",
        ])

        for emp in Employee.objects.all():
            writer.writerow([
                emp.employee_code,
                emp.first_name,
                emp.last_name or "",
                emp.email or "",
                emp.department,
                emp.designation,
                emp.location or "",
                emp.phone or "",
                emp.date_of_joining or "",
                emp.status,
                emp.created_at,
                emp.updated_at,
            ])

        return response
