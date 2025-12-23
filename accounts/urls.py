# accounts/urls.py
from django.urls import path, include

from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet
from django.urls import path
from .views import (
   login_view, reset_password,
    EmployeeViewSet
)

# -------------------------
# EmployeeViewSet Mappings
# -------------------------

employee_list_create = EmployeeViewSet.as_view({
    "get": "list",
    "post": "create",
})

employee_retrieve = EmployeeViewSet.as_view({
    "get": "retrieve",
})

employee_update = EmployeeViewSet.as_view({
    "put": "update",
})

employee_patch = EmployeeViewSet.as_view({
    "patch": "partial_update",
})

employee_delete = EmployeeViewSet.as_view({
    "delete": "destroy",
})

employee_bulk_upload = EmployeeViewSet.as_view({
    "post": "bulk_upload",
})

employee_export = EmployeeViewSet.as_view({
    "get": "export_employees",
})

employee_stats = EmployeeViewSet.as_view({
    "get": "stats",
})


router = DefaultRouter()
router.register(r"employees", EmployeeViewSet, basename="employee")

urlpatterns = [
    # AUTH APIs
   path('login/', login_view),
    path('reset-password/', reset_password),
    

    # EMPLOYEE CRUD APIs (NO "api/" HERE!)
    path("employees/", employee_list_create),                   # GET + POST
    path("employees/<int:pk>/", employee_retrieve),             # GET
    path("employees/<int:pk>/update/", employee_update),        # PUT
    path("employees/<int:pk>/patch/", employee_patch),          # PATCH
    path("employees/<int:pk>/delete/", employee_delete),        # DELETE

    # EXTRA APIs
    path("employees/bulk-upload/", employee_bulk_upload),
    path("employees/export/", employee_export),
    path("employees/stats/", employee_stats),
]