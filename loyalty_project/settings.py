"""
Django settings for loyalty microservice project.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass  # python-dotenv not installed, use environment variables directly

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']  # Configure properly for production

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',  # CORS support
    'rest_framework',
    'rest_framework.authtoken',  # Token authentication
    'loyalty',
    'apps.shared',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware (must be before CommonMiddleware)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'loyalty_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'loyalty_project.wsgi.application'

# Database
# Temporarily use SQLite for migrations if psycopg2 not available
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'True') == 'True'

try:
    import psycopg2
    psycopg2_available = True
except ImportError:
    psycopg2_available = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("psycopg2 not available, using SQLite for migrations. Install psycopg2-binary for PostgreSQL.")

if USE_POSTGRES and psycopg2_available:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'loyalty_db'),
            'USER': os.environ.get('DB_USER', 'loyalty_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'loyalty_password'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    # Fallback to SQLite for migrations
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Allow unauthenticated access in development
    # In production, remove this or set to False
    'UNAUTHENTICATED_USER': None,
}

# DWH Configuration (from settings_template.py - configure as needed)
DWH_TYPE = os.environ.get('DWH_TYPE', 'postgresql')
# Connection string for DWH PostgreSQL database (separate from Django database)
DWH_POSTGRES_CONNECTION_STRING = os.environ.get('DWH_POSTGRES_CONNECTION_STRING', 'postgresql://postgres:root123@localhost:5432/DWH')
DWH_CUSTOMER_FEATURES_QUERY = os.environ.get('DWH_CUSTOMER_FEATURES_QUERY', None)
DWH_CUSTOMER_FEATURES_TABLE = os.environ.get('DWH_CUSTOMER_FEATURES_TABLE', 'customer_features_view')

# ML Configuration
# Mock ML Mode - DISABLED - System uses real ML models only
# Set ML_MOCK_MODE=True in environment to enable (NOT RECOMMENDED)
ML_MOCK_MODE = False  # Always False - no mock mode

# Kafka Configuration (for gamification event streaming)
KAFKA_ENABLED = os.environ.get('KAFKA_ENABLED', 'False').lower() == 'true'
KAFKA_BOOTSTRAP_SERVERS = os.environ.get(
    'KAFKA_BOOTSTRAP_SERVERS',
    'localhost:9092'
).split(',')
KAFKA_CUSTOMER_EVENTS_TOPICS = ['customer-events']  # Topics to consume from
KAFKA_CONSUMER_GROUP = 'loyalty-gamification-consumer'  # Consumer group ID

# ML Model Input Size - Number of features expected by ML models
# Default: 10 features (standard model configuration)
# This will be auto-calculated from ML_FEATURE_MAPPING if not set via environment variable
ML_MODEL_INPUT_SIZE = int(os.environ.get('ML_MODEL_INPUT_SIZE', '0'))  # 0 = auto-calculate

# ML Feature Mapping - Maps DWH column names to ML model feature names
# Can be configured via .env file as JSON string: ML_FEATURE_MAPPING='{"revenue":"total_revenue",...}'
ml_feature_mapping_env = os.environ.get('ML_FEATURE_MAPPING', '')
if ml_feature_mapping_env:
    try:
        ML_FEATURE_MAPPING = json.loads(ml_feature_mapping_env)
    except json.JSONDecodeError:
        logger.warning(f"Invalid ML_FEATURE_MAPPING JSON, using default")
        ML_FEATURE_MAPPING = {
            'revenue': 'total_revenue',
            'transaction_count': 'transaction_count',
            'days_since_last': 'days_since_last_transaction',
            'avg_transaction_value': 'avg_transaction_value',
            'lifetime_value': 'lifetime_value',
        }
else:
    # Default feature mapping - 10 features for standard ML models
    ML_FEATURE_MAPPING = {
        'revenue': 'total_revenue',
        'transaction_count': 'transaction_count',
        'days_since_last': 'days_since_last_transaction',
        'avg_transaction_value': 'avg_transaction_value',
        'lifetime_value': 'lifetime_value',
        'customer_age_days': 'customer_age_days',
        'monthly_revenue': 'monthly_revenue',
        'product_count': 'product_count',
        'service_count': 'service_count',
        'engagement_score': 'engagement_score',
    }
# Ensure ML_MODEL_INPUT_SIZE matches the number of features in ML_FEATURE_MAPPING
# If ML_MODEL_INPUT_SIZE was set to 0 (auto-calculate), use feature mapping count
if ML_MODEL_INPUT_SIZE == 0:
    ML_MODEL_INPUT_SIZE = len(ML_FEATURE_MAPPING) if ML_FEATURE_MAPPING else 10
ML_MODEL_NBO_PATH = 'models/nbo.tflite'
ML_MODEL_CHURN_PATH = 'models/churn.tflite'

# Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_FEATURE_STORE_DB = int(os.environ.get('REDIS_FEATURE_STORE_DB', '1'))

# Kafka
LOYALTY_KAFKA_ENABLED = os.environ.get('LOYALTY_KAFKA_ENABLED', 'False') == 'True'
LOYALTY_KAFKA_BOOTSTRAP_SERVERS = os.environ.get('LOYALTY_KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
LOYALTY_KAFKA_GROUP_ID = os.environ.get('LOYALTY_KAFKA_GROUP_ID', 'loyalty-service')

# External System Integration - Xiva BSS
# Configure these in your .env file or environment variables
XIVA_API_BASE_URL = os.environ.get('XIVA_API_BASE_URL', 'https://www.xiva.ca/api')
XIVA_API_AUTH_TYPE = os.environ.get('XIVA_API_AUTH_TYPE', 'JWT')  # 'JWT', 'Token', or 'Bearer'
XIVA_API_USERNAME = os.environ.get('XIVA_API_USERNAME', '')  # For JWT authentication
XIVA_API_PASSWORD = os.environ.get('XIVA_API_PASSWORD', '')  # For JWT authentication
XIVA_API_AUTH_TOKEN = os.environ.get('XIVA_API_AUTH_TOKEN', '')  # For Token/Bearer authentication
XIVA_API_TIMEOUT = int(os.environ.get('XIVA_API_TIMEOUT', '30'))

# Legacy customer API (for backward compatibility)
LOYALTY_CUSTOMER_API_BASE_URL = os.environ.get('LOYALTY_CUSTOMER_API_BASE_URL', '')
LOYALTY_CUSTOMER_API_AUTH_TOKEN = os.environ.get('LOYALTY_CUSTOMER_API_AUTH_TOKEN', '')

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

# Allow credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# Allow all methods
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Allow all headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

