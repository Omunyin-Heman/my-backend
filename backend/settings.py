import os
from pathlib import Path
from dotenv import load_dotenv
from decouple import config
import dj_database_url

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()

# --------------------------------------------------
# Base directory
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# Security & Debug
# --------------------------------------------------
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-rhfqwmp84v_(h*=!ca=x%)=sjxxm6n3b*^i@o64e5b814!_!t8'
)
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Restrict allowed hosts
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

# --------------------------------------------------
# Installed apps
# --------------------------------------------------
INSTALLED_APPS = [
    # Django default
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'corsheaders',
    'rest_framework',

    # Local apps
    'partnerApplications',
    'volunteers',
    'payments',
    'contacts',
]

# --------------------------------------------------
# Middleware
# --------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be first
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --------------------------------------------------
# CORS & CSRF
# --------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://epicare-frontend.vercel.app",
    "https://my-backend-1-8oq8.onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://epicare-frontend.vercel.app",
    "https://my-backend-1-8oq8.onrender.com",
]

CORS_ALLOW_CREDENTIALS = True

# --------------------------------------------------
# URLs & WSGI
# --------------------------------------------------
ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'

# --------------------------------------------------
# Database
# --------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL')
    )
}

# --------------------------------------------------
# Password Validation
# --------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------
# Internationalization
# --------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------
# Static & Media
# --------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --------------------------------------------------
# Default primary key field
# --------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------
# PayPal
# --------------------------------------------------
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_SECRET = os.getenv('PAYPAL_SECRET')
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')

PAYPAL_CALLBACK_URL = os.getenv(
    'PAYPAL_CALLBACK_URL',
    'https://my-backend-1-8oq8.onrender.com/api/payments/paypal/'
)

# --------------------------------------------------
# M-Pesa
# --------------------------------------------------
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
MPESA_BASE_URL = os.getenv('MPESA_BASE_URL')

MPESA_CALLBACK_URL = os.getenv(
    'MPESA_CALLBACK_URL',
    'https://my-backend-1-8oq8.onrender.com/api/payments/mpesa/callback/'
)
