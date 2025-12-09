from pathlib import Path
from datetime import timedelta

# ---------------- BASE DIR ----------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------- SECURITY ----------------
SECRET_KEY = 'django-insecure-l!iglopb%y5=r81%+msczfnfv2c!urqronv33-ls(bz(l08d=p'
DEBUG = True
ALLOWED_HOSTS = []

# ---------------- APPS ----------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'accounts',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'drf_spectacular',
]

# ---------------- MIDDLEWARE ----------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ---------------- URLS ----------------
ROOT_URLCONF = 'backend.urls'

# ---------------- TEMPLATES ----------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ---------------- WSGI ----------------
WSGI_APPLICATION = 'backend.wsgi.application'

# ---------------- DATABASE ----------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'sslmode': 'require',
        },
        'NAME': 'neondb',
        'USER': 'neondb_owner',
        'PASSWORD': 'npg_DWHgMiBR0jZ8',
        'HOST': 'ep-fancy-smoke-ad0qryk6-pooler.c-2.us-east-1.aws.neon.tech',
        'PORT': '5432',
    }
}

# ---------------- PASSWORD VALIDATORS ----------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------- INTERNATIONALIZATION ----------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------- STATIC FILES ----------------
STATIC_URL = 'static/'

# ---------------- CUSTOM USER ----------------
AUTH_USER_MODEL = 'accounts.User'

# ---------------- REST FRAMEWORK ----------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ---------------- SIMPLE JWT ----------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ---------------- EMAIL CONFIG (OTP) ----------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # prints OTP in console
DEFAULT_FROM_EMAIL = 'noreply@hrms.com'

# ---------------- DRF SPECTACULAR ----------------
SPECTACULAR_SETTINGS = {
    'TITLE': 'HRMS API',
    'DESCRIPTION': 'HRMS project API documentation',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
