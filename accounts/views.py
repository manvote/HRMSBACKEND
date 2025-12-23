# accounts/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

User = get_user_model()

@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"error": "Email and password required"}, status=400)

    # ✅ Email-based authentication
    user = authenticate(request, email=email, password=password)

    if not user:
        return Response({"error": "Invalid credentials"}, status=401)

    if not (user.is_superuser or user.is_super_admin):
        return Response({"error": "Access denied"}, status=403)

    refresh = RefreshToken.for_user(user)

    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "first_login": user.first_login,
        "redirect": "reset-password" if user.first_login else "dashboard"
    })






@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reset_password(request):
    user = request.user
    new_password = request.data.get("new_password")

    if not new_password:
        return Response({"error": "New password required"}, status=400)

    user.set_password(new_password)
    user.first_login = False
    user.save()

    return Response({"message": "Password updated successfully"})






# ============================================================
# Employee Module 
# ============================================================
# ============================
# Employee Module
# ============================

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes

from django.db.models import Q, Count
from django.http import HttpResponse
import csv, io

from .models import Employee
from .serializers import EmployeeSerializer


@extend_schema_view(
    create=extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "employee_code": {"type": "string"},
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "email": {"type": "string"},
                    "department": {"type": "string"},
                    "designation": {"type": "string"},
                    "location": {"type": "string"},
                    "phone": {"type": "string"},
                    "status": {"type": "string"},
                    "date_of_joining": {"type": "string", "format": "date"},
                    "photo": {"type": "string", "format": "binary"},
                }
            }
        }
    ),

    # ✅ ADD THIS (FOR PUT)
    update=extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "employee_code": {"type": "string"},
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "email": {"type": "string"},
                    "department": {"type": "string"},
                    "designation": {"type": "string"},
                    "location": {"type": "string"},
                    "phone": {"type": "string"},
                    "status": {"type": "string"},
                    "date_of_joining": {"type": "string", "format": "date"},
                    "photo": {"type": "string", "format": "binary"},
                }
            }
        }
    ),

    # PATCH already works
    partial_update=extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "photo": {"type": "string", "format": "binary"}
                }
            }
        }
    ),
)
class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Employee.objects.all().order_by("employee_code")
    serializer_class = EmployeeSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        if self.action == "list" and self.request.query_params:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        qs = Employee.objects.all()
        params = self.request.query_params

        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_code__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )

        for field in ["department", "status", "location"]:
            if params.get(field):
                qs = qs.filter(**{f"{field}__iexact": params[field]})

        return qs

    # ---------- STATS ----------
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

    # ---------- BULK UPLOAD ----------
    # ---------- BULK UPLOAD (CSV + XLSX) ----------
    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"}
                },
                "required": ["file"]
            }
        },
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["post"], url_path="bulk-upload")
    def bulk_upload(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        rows = []
        filename = file.name.lower()

        try:
            if filename.endswith(".csv"):
                decoded = file.read().decode("utf-8")
                reader = csv.DictReader(io.StringIO(decoded))
                rows = list(reader)

            elif filename.endswith(".xlsx"):
                import openpyxl
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                headers = [cell.value for cell in sheet[1]]
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    rows.append(dict(zip(headers, row)))
            else:
                return Response(
                    {"error": "Only CSV or XLSX files are supported"},
                    status=400
                )

        except Exception as e:
            return Response({"error": str(e)}, status=400)

        created, updated, errors = 0, 0, []

        for idx, row in enumerate(rows, start=1):
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

        return Response({
            "created": created,
            "updated": updated,
            "errors": errors
        })

    # ---------- EXPORT ----------
    @action(detail=False, methods=["get"], url_path="export")
    def export_employees(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=employees.csv"

        writer = csv.writer(response)
        writer.writerow([f.name for f in Employee._meta.fields])

        for emp in Employee.objects.all():
            writer.writerow([getattr(emp, f.name) for f in Employee._meta.fields])

        return response