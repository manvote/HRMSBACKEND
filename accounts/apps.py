from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'


# ==========================
# Employee Module 
# (Not registered in INSTALLED_APPS, so safe to keep here)
# ==========================
class EmployeesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "employees"
    label = "employees"