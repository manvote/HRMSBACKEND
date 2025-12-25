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
from .serializers import (
    LoginSerializer,
    LoginResponseSerializer,
    ResetPasswordSerializer,
    MessageResponseSerializer
)

User = get_user_model()

@extend_schema(
    request=LoginSerializer,
    responses={
        200: LoginResponseSerializer,
        400: MessageResponseSerializer,
        401: MessageResponseSerializer,
        403: MessageResponseSerializer,
    },
    description="Login endpoint for superusers and super admins",
    tags=["Authentication"]
)
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




@extend_schema(
    request=ResetPasswordSerializer,
    responses={
        200: MessageResponseSerializer,
        400: MessageResponseSerializer,
    },
    description="Reset password for authenticated user",
    tags=["Authentication"]
)
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




#------employee  module -------

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q, Count
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from datetime import date
import csv, io
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Employee, EmployeeOffboarding, OffboardingChecklist
from .serializers import EmployeeOffboardingSerializer,OffboardingChecklistSerializer
from django.http import FileResponse
from .models import EmployeeDocument
from .serializers import EmployeeDocumentSerializer
from django.http import FileResponse
import os
from .serializers import (
   
    EmployeeSerializer,
    EmployeeOffboardingSerializer,
    EmployeeOverviewSerializer,
    EmployeeJobSerializer,
    EmployeeSalarySerializer,
)

# =================================================
# EMPLOYEE LIST + CREATE (PHOTO + GENDER + DOB)
# =================================================
class EmployeeListCreateView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        # 🔓 Public ONLY for filter/search APIs
        if self.request.method == "GET" and self.request.query_params:
            return []
        # 🔐 Base list & create require auth
        return [IsAuthenticated()]

    @extend_schema(
        request={
            "multipart/form-data": {
            "type": "object",
            "properties": {
                # BASIC INFO
                "employee_code": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "email": {"type": "string"},
                "gender": {
                    "type": "string",
                    "enum": ["MALE", "FEMALE", "OTHER"]
                },
                "date_of_birth": {"type": "string", "format": "date"},

                # JOB INFO
                "department": {"type": "string"},
                "designation": {"type": "string"},
                "location": {"type": "string"},
                "phone": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["ACTIVE", "ON_LEAVE", "INACTIVE"]
                },
                "date_of_joining": {"type": "string", "format": "date"},

                # NEW HR FIELDS 🔥
                "reporting_manager": {
                    "reporting_manager": {
                    "type": "string",
                     "example": "Priya Sharma",
                     "description": "Full name of reporting manager"
                   }

                },
                "employee_type": {
                    "type": "string",
                    "enum": ["FULL_TIME", "TEMPORARY"]
                },
                "work_shift": {
                    "type": "string",
                    "enum": ["DAY", "NIGHT", "ROTATIONAL"]
                },
                "work_timing": {
                    "type": "string",
                    "example": "09:00 AM - 06:00 PM"
                },
                "probation_status": {
                    "type": "string",
                    "enum": ["PENDING", "COMPLETED"]
                },

                # SALARY 💰
                "annual_ctc": {"type": "number", "format": "decimal"},
                "basic_pay": {"type": "number", "format": "decimal"},
                "allowances": {"type": "number", "format": "decimal"},
                "bonus": {"type": "number", "format": "decimal"},

                # PHOTO
                "photo": {
                    "type": "string",
                    "format": "binary"
                },
            }
        }
    },
        responses=EmployeeSerializer
    )
    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    def get(self, request):
        qs = Employee.objects.all().order_by("employee_code")
        params = request.query_params

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

        return Response(EmployeeSerializer(qs, many=True).data)
    
# =================================================
# EMPLOYEE FILTER APIs (PUBLIC)
# =================================================
class EmployeeFilterView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, filter_type):
        if filter_type == "departments":
            data = Employee.objects.values_list("department", flat=True).distinct()
        elif filter_type == "locations":
            data = Employee.objects.values_list("location", flat=True).distinct()
        elif filter_type == "status":
            data = Employee.objects.values_list("status", flat=True).distinct()
        else:
            return Response(
                {"error": "Use departments | locations | status"},
                status=400
            )

        return Response(list(filter(None, data)))


# =================================================
# EMPLOYEE RETRIEVE
# =================================================
class EmployeeRetrieveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        emp = Employee.objects.get(pk=pk)
        return Response(EmployeeSerializer(emp).data)


class EmployeeOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = Employee.objects.get(pk=pk)
        serializer = EmployeeOverviewSerializer(employee)
        return Response(serializer.data)

class EmployeeJobView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = Employee.objects.get(pk=pk)
        serializer = EmployeeJobSerializer(employee)
        return Response(serializer.data)

class EmployeeSalaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = Employee.objects.get(pk=pk)
        serializer = EmployeeSalarySerializer(employee)
        return Response(serializer.data)
    

class EmployeeOverviewUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=EmployeeOverviewSerializer,
        responses=EmployeeOverviewSerializer,
        tags=["Employee"],
        description="Update employee overview details"
    )
    def put(self, request, pk):
        employee = Employee.objects.get(pk=pk)

        serializer = EmployeeOverviewSerializer(
            employee,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)



class EmployeeJobUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=EmployeeJobSerializer,
        responses=EmployeeJobSerializer,
        tags=["Employee"],
        description="Update employee job details"
    )
    def put(self, request, pk):
        employee = Employee.objects.get(pk=pk)

        serializer = EmployeeJobSerializer(
            employee,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

class EmployeeSalaryUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=EmployeeSalarySerializer,
        responses=EmployeeSalarySerializer,
        tags=["Employee"],
        description="Update employee salary details"
    )
    def put(self, request, pk):
        employee = Employee.objects.get(pk=pk)

        serializer = EmployeeSalarySerializer(
            employee,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


# =================================================
# EMPLOYEE UPDATE (PUT ONLY)
# =================================================
class EmployeeUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        request={
            "multipart/form-data": {
            "type": "object",
            "properties": {

                # BASIC DETAILS
                "employee_code": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "email": {"type": "string"},
                "gender": {"type": "string", "enum": ["MALE", "FEMALE", "OTHER"]},
                "date_of_birth": {"type": "string", "format": "date"},

                "department": {"type": "string"},
                "designation": {"type": "string"},
                "location": {"type": "string"},
                "phone": {"type": "string"},
                "status": {"type": "string", "enum": ["ACTIVE", "ON_LEAVE", "INACTIVE"]},
                "date_of_joining": {"type": "string", "format": "date"},

                # 🔥 NEW HR FIELDS
                "reporting_manager": {
                    "type": "integer",
                    "description": "Employee ID of reporting manager"
                },

                "employee_type": {
                    "type": "string",
                    "enum": ["FULL_TIME", "TEMPORARY"]
                },

                "work_shift": {
                    "type": "string",
                    "enum": ["DAY", "NIGHT", "ROTATIONAL"]
                },

                "work_timing": {
                    "type": "string",
                    "example": "09:00 AM - 06:00 PM"
                },

                "probation_status": {
                    "type": "string",
                    "enum": ["PENDING", "COMPLETED"]
                },

                # 💰 SALARY
                "annual_ctc": {"type": "number"},
                "basic_pay": {"type": "number"},
                "allowances": {"type": "number"},
                "bonus": {"type": "number"},

                # FILE
                "photo": {"type": "string", "format": "binary"},
            }
        }
    },
        responses=EmployeeSerializer
    )
    def put(self, request, pk):
        emp = Employee.objects.get(pk=pk)
        serializer = EmployeeSerializer(emp, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# =================================================
# EMPLOYEE PATCH (PHOTO / PARTIAL)
# =================================================
class EmployeePatchView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "photo": {"type": "string", "format": "binary"}  # ✅ FILE
                }
            }
        },
        responses=EmployeeSerializer
    )
    def patch(self, request, pk):
        emp = Employee.objects.get(pk=pk)
        serializer = EmployeeSerializer(emp, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# =================================================
# EMPLOYEE DELETE
# =================================================
class EmployeeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        Employee.objects.filter(pk=pk).delete()
        return Response({"message": "Employee deleted"})


# =================================================
# EMPLOYEE BULK UPLOAD (CSV)
# =================================================
class EmployeeBulkUploadView(APIView):
    permission_classes = [IsAuthenticated]

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
        responses=OpenApiTypes.OBJECT
    )
    def post(self, request):
        file = request.FILES.get("file")
        if not file or not file.name.endswith(".csv"):
            return Response({"error": "CSV file required"}, status=400)

        decoded = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))

        created, updated, errors = 0, 0, []

        for idx, row in enumerate(reader, start=1):
            try:
                _, is_created = Employee.objects.update_or_create(
                    employee_code=row.get("employee_code"),
                    defaults=row
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


# =================================================
# EMPLOYEE STATS
# =================================================
class EmployeeStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Employee.objects.all()
        return Response({
            "total_employees": qs.count(),
            "active": qs.filter(status="ACTIVE").count(),
            "on_leave": qs.filter(status="ON_LEAVE").count(),
            "department_breakdown": list(
                qs.values("department").annotate(count=Count("id"))
            )
        })


# =================================================
# EMPLOYEE EXPORT (CSV DOWNLOAD)
# =================================================
class EmployeeExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=employees.csv"

        writer = csv.writer(response)
        writer.writerow([f.name for f in Employee._meta.fields])

        for emp in Employee.objects.all():
            writer.writerow([getattr(emp, f.name) for f in Employee._meta.fields])

        return response


# =================================================
# EMPLOYEE OFFBOARDING API
# =================================================
class EmployeeOffboardingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "resignation_date": {"type": "string", "format": "date"},
                    "last_working_date": {"type": "string", "format": "date"},
                    "reason_for_exit": {"type": "string"},
                    "additional_notes": {"type": "string"},
                    "checklist": {
                        "type": "object",
                        "properties": {
                            "LAPTOP_RETURNED": {
                                "type": "string",
                                "enum": ["PENDING", "SUBMITTED"]
                            },
                            "ACCESS_CARD": {
                                "type": "string",
                                "enum": ["PENDING", "SUBMITTED"]
                            },
                            "DOCUMENTS": {
                                "type": "string",
                                "enum": ["PENDING", "SUBMITTED"]
                            },
                            "NO_DUES": {
                                "type": "string",
                                "enum": ["PENDING", "SUBMITTED"]
                            },
                            "KNOWLEDGE_TRANSFER": {
                                "type": "string",
                                "enum": ["PENDING", "SUBMITTED"]
                            },
                        }
                    }
                },
                "required": [
                    "resignation_date",
                    "last_working_date",
                    "reason_for_exit",
                    "checklist"
                ]
            }
        },
        responses=EmployeeOffboardingSerializer,
        tags=["Employee Offboarding"],
        description="Create employee offboarding with checklist"
    )
    def post(self, request, pk):

        # 1️⃣ Check employee exists
        try:
            employee = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee not found"},
                status=404
            )

        # 2️⃣ Prevent duplicate offboarding
        if EmployeeOffboarding.objects.filter(employee=employee).exists():
            return Response(
                {"error": "Offboarding already exists for this employee"},
                status=400
            )

        data = request.data
        checklist_data = data.get("checklist")

        if not checklist_data:
            return Response(
                {"error": "Checklist data is required"},
                status=400
            )

        # 3️⃣ Create offboarding record
        offboarding = EmployeeOffboarding.objects.create(
            employee=employee,
            resignation_date=data["resignation_date"],
            last_working_date=data["last_working_date"],
            reason_for_exit=data["reason_for_exit"],
            additional_notes=data.get("additional_notes", "")
        )

        # 4️⃣ 🔥 IMPORTANT FIX (THIS IS THE ROOT CAUSE)
        # DELETE any existing checklist rows first
        OffboardingChecklist.objects.filter(offboarding=offboarding).delete()

        ALLOWED_ITEMS = [
            "LAPTOP_RETURNED",
            "ACCESS_CARD",
            "DOCUMENTS",
            "NO_DUES",
            "KNOWLEDGE_TRANSFER"
        ]
        ALLOWED_STATUS = ["PENDING", "SUBMITTED"]

        for item, status in checklist_data.items():
            item = item.upper()
            status = status.upper()

            if item not in ALLOWED_ITEMS:
                return Response(
                    {"error": f"Invalid checklist item: {item}"},
                    status=400
                )

            if status not in ALLOWED_STATUS:
                return Response(
                    {
                        "error": (
                            f"Invalid status '{status}' for {item}. "
                            f"Allowed values: PENDING or SUBMITTED"
                        )
                    },
                    status=400
                )

            OffboardingChecklist.objects.create(
                offboarding=offboarding,
                item=item,
                status=status
            )

        # 5️⃣ Success
        return Response(
            EmployeeOffboardingSerializer(offboarding).data,
            status=201
        )

# =================================================
# UPDATE OFFBOARDING CHECKLIST
# =================================================
class OffboardingChecklistUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    # ✅ GET CHECKLIST DETAILS USING checklist_id
    def get(self, request, checklist_id):
        try:
            checklist_item = OffboardingChecklist.objects.select_related(
                "offboarding"
            ).get(id=checklist_id)
        except OffboardingChecklist.DoesNotExist:
            return Response(
                {"error": "Checklist item not found"},
                status=404
            )

        # Fetch all checklist items for same offboarding
        checklist_qs = OffboardingChecklist.objects.filter(
            offboarding=checklist_item.offboarding
        )

        checklist_data = {
            item.item: item.status
            for item in checklist_qs
        }

        return Response({
            "checklist": checklist_data
        })

# =================================================
# DEACTIVATE EMPLOYEE
# =================================================
class EmployeeDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        emp = Employee.objects.get(pk=pk)
        emp.status = "INACTIVE"
        emp.save()

        return Response({"message": "Employee deactivated"})

class EmployeeFinalSettlementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        pending_salary = 75000
        leave_encashment = 25000
        gratuity = 50000
        deductions = 35000

        total = pending_salary + leave_encashment + gratuity - deductions

        return Response({
            "pending_salary": pending_salary,
            "leave_encashment": leave_encashment,
            "gratuity": gratuity,
            "deductions": deductions,
            "total_settlement": total
        })


class EmployeeDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "document_type": {
                        "type": "string",
                        "enum": ["RESUME", "ID_PROOF", "OFFER_LETTER", "EXPERIENCE"]
                    },
                    "file": {
                        "type": "string",
                        "format": "binary"
                    }
                },
                "required": ["document_type", "file"]
            }
        },
        responses=EmployeeDocumentSerializer
    )
    def post(self, request, emp_id):
        employee = Employee.objects.get(id=emp_id)

        doc, _ = EmployeeDocument.objects.update_or_create(
            employee=employee,
            document_type=request.data["document_type"],
            defaults={"file": request.FILES["file"]}
        )

        return Response(
            EmployeeDocumentSerializer(doc).data,
            status=201
        )

class EmployeeDocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, emp_id):
        docs = EmployeeDocument.objects.filter(employee_id=emp_id)

        return Response({
            "employee_id": emp_id,
            "documents": EmployeeDocumentSerializer(docs, many=True).data
        })

class EmployeeDocumentDownloadByTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, emp_id, document_type):
        try:
            document = EmployeeDocument.objects.get(
                employee_id=emp_id,
                document_type=document_type.upper()
            )
        except EmployeeDocument.DoesNotExist:
            return Response(
                {"error": "Document not found for this employee"},
                status=404
            )

        return FileResponse(
            document.file.open("rb"),
            as_attachment=True,
            filename=document.file.name.split("/")[-1]
        )

# ================================
# BULK DELETE EMPLOYEES
# ================================
from .serializers import EmployeeBulkActionSerializer

class EmployeeBulkDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=EmployeeBulkActionSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Bulk delete selected employees"
    )
    def post(self, request):
        employee_ids = request.data.get("employee_ids", [])

        if not employee_ids:
            return Response(
                {"error": "employee_ids is required"},
                status=400
            )

        deleted_count, _ = Employee.objects.filter(
            id__in=employee_ids
        ).delete()

        return Response({
            "deleted_count": deleted_count
        })

# ================================
# BULK EXPORT EMPLOYEES (CSV)
# ================================
class EmployeeBulkExportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=EmployeeBulkActionSerializer,
        responses={200: OpenApiTypes.BINARY},
        description="Export selected employees as CSV"
    )
    def post(self, request):
        employee_ids = request.data.get("employee_ids", [])

        if not employee_ids:
            return Response(
                {"error": "employee_ids is required"},
                status=400
            )

        employees = Employee.objects.filter(id__in=employee_ids)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            "attachment; filename=selected_employees.csv"
        )

        writer = csv.writer(response)
        writer.writerow([
            "ID",
            "Employee Code",
            "First Name",
            "Last Name",
            "Email",
            "Department",
            "Designation",
            "Location",
            "Status",
        ])

        for emp in employees:
            writer.writerow([
                emp.id,
                emp.employee_code,
                emp.first_name,
                emp.last_name,
                emp.email,
                emp.department,
                emp.designation,
                emp.location,
                emp.status,
            ])

        return response


class EmployeeSalarySlipDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="Employee ID"
            )
        ],
        responses={200: OpenApiTypes.BINARY},
        description="Download employee salary slip as PDF"
    )
    def get(self, request, id):
        try:
            employee = Employee.objects.get(pk=id)
        except Employee.DoesNotExist:
            return Response(
                {"error": "Employee not found"},
                status=404
            )

        # ---- PDF RESPONSE ----
        response = HttpResponse(content_type="application/pdf")
        filename = f"salary_slip_{employee.employee_code}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        y = height - 50

        # ---- HEADER ----
        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(width / 2, y, "SALARY SLIP")
        y -= 40

        p.setFont("Helvetica", 11)
        p.drawString(50, y, f"Date: {date.today().strftime('%d-%m-%Y')}")
        y -= 30

        # ---- EMPLOYEE DETAILS ----
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Employee Details")
        y -= 20

        p.setFont("Helvetica", 11)
        p.drawString(50, y, f"Employee Code: {employee.employee_code}")
        y -= 18
        p.drawString(50, y, f"Name: {employee.first_name} {employee.last_name}")
        y -= 18
        p.drawString(50, y, f"Designation: {employee.designation}")
        y -= 18
        p.drawString(50, y, f"Department: {employee.department}")
        y -= 30

        # ---- SALARY DETAILS ----
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Salary Details")
        y -= 20

        p.setFont("Helvetica", 11)
        p.drawString(50, y, f"Annual CTC: ₹ {employee.annual_ctc}")
        y -= 18
        p.drawString(50, y, f"Basic Pay: ₹ {employee.basic_pay}")
        y -= 18
        p.drawString(50, y, f"Allowances: ₹ {employee.allowances}")
        y -= 18
        p.drawString(50, y, f"Bonus: ₹ {employee.bonus}")
        y -= 30
        # ---- FOOTER ----
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(50, y, "This is a system-generated salary slip.")
        p.showPage()
        p.save()
        return response
