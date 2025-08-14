"""
Production settings for TravelsKe project.
This file contains production-specific configurations including WhiteNoise optimization.
"""

from .settings import *

# Production settings
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'localhost', '127.0.0.1']

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# WhiteNoise Production Configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# WhiteNoise production settings
WHITENOISE_USE_FINDERS = False  # Disable in production for better performance
WHITENOISE_AUTOREFRESH = False  # Disable auto-refresh in production
WHITENOISE_MAX_AGE = 31536000  # 1 year cache for static files

# Add compression and caching headers
WHITENOISE_ADD_HEADERS_FUNCTION = 'travelske.settings_production.add_headers'

# Database - Use your production database settings here
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'your_production_db',
#         'USER': 'your_db_user',
#         'PASSWORD': 'your_db_password',
#         'HOST': 'your_db_host',
#         'PORT': '3306',
#     }
# }

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.your-email-provider.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@your-domain.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@your-domain.com'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}

def add_headers(headers, path, url):
    """
    Add custom headers for static files served by WhiteNoise.
    This function is called by WhiteNoise for each static file.
    """
    # Add cache control headers for different file types
    if path.endswith('.css') or path.endswith('.js'):
        headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    elif path.endswith('.png') or path.endswith('.jpg') or path.endswith('.jpeg') or path.endswith('.gif'):
        headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    elif path.endswith('.ico'):
        headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    else:
        headers['Cache-Control'] = 'public, max-age=86400'  # 1 day 