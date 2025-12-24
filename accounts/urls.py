# accounts/urls.py
from django.urls import path, include


from django.urls import path
from .views import (
   login_view, reset_password
)

from django.urls import path

from .views import (
    # Employee
    
    EmployeeListCreateView,
    EmployeeRetrieveView,
    EmployeeUpdateView,
    EmployeePatchView,
    EmployeeDeleteView,
    EmployeeFilterView,
    EmployeeBulkUploadView,
    EmployeeStatsView,
    EmployeeExportView,

    EmployeeOverviewView,
    EmployeeJobView,
    EmployeeSalaryView,
    

    # Offboarding
    EmployeeOffboardingView,
    OffboardingChecklistUpdateView,
    EmployeeFinalSettlementView,
    EmployeeDeactivateView,
    EmployeeDocumentUploadView,
    EmployeeDocumentListView,
    EmployeeDocumentDownloadByTypeView,
    EmployeeOverviewUpdateView,
    EmployeeJobUpdateView,
    EmployeeSalaryUpdateView,
    EmployeeBulkDeleteView,
    EmployeeBulkExportView,
    EmployeeSalarySlipDownloadView
)
urlpatterns = [
    # AUTH APIs
   path('login/', login_view),
    path('reset-password/', reset_password),
    

     # ================= EMPLOYEE =================
    path("employees/", EmployeeListCreateView.as_view()),
    path("employees/<int:pk>/", EmployeeRetrieveView.as_view()),

    path("employees/<int:pk>/update/", EmployeeUpdateView.as_view()),
    path("employees/<int:pk>/patch/", EmployeePatchView.as_view()),
    path("employees/<int:pk>/delete/", EmployeeDeleteView.as_view()),

    # ================= FILTER =================
    path("employees/filter/<str:filter_type>/", EmployeeFilterView.as_view()),

    # ================= BULK / STATS =================
    path("employees/bulk-upload/", EmployeeBulkUploadView.as_view()),
    path("employees/export/", EmployeeExportView.as_view()),
    path("employees/stats/", EmployeeStatsView.as_view()),

    # ================= OFFBOARDING =================
    path("employees/<int:pk>/offboarding/", EmployeeOffboardingView.as_view()),
    path(
        "employees/offboarding/checklist/<int:checklist_id>/",
        OffboardingChecklistUpdateView.as_view()
    ),
    path(
        "employees/<int:pk>/final-settlement/",
        EmployeeFinalSettlementView.as_view()
    ),
    path(
        "employees/<int:pk>/deactivate/",
        EmployeeDeactivateView.as_view()
    ),
    path("employees/<int:pk>/overview/", EmployeeOverviewView.as_view()),
    path("employees/<int:pk>/job/", EmployeeJobView.as_view()),
    path("employees/<int:pk>/salary/", EmployeeSalaryView.as_view()),
    path("employees/<int:pk>/overview/update/", EmployeeOverviewUpdateView.as_view()),
    path("employees/<int:pk>/job/update/", EmployeeJobUpdateView.as_view()),
    path("employees/<int:pk>/salary/update/", EmployeeSalaryUpdateView.as_view()),

    # 📄 EMPLOYEE DOCUMENTS
    path("employees/<int:emp_id>/documents/upload/", EmployeeDocumentUploadView.as_view() ),
    path("employees/<int:emp_id>/documents/",EmployeeDocumentListView.as_view()),
    path("employees/<int:emp_id>/documents/download/<str:document_type>/",EmployeeDocumentDownloadByTypeView.as_view()),
    path("employees/bulk-delete/", EmployeeBulkDeleteView.as_view()),
    path("employees/bulk-export/", EmployeeBulkExportView.as_view()),
    path(
    "employees/<int:id>/salary-slip/download/",EmployeeSalarySlipDownloadView.as_view()),


]
