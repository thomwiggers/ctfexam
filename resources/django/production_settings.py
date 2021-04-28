import os
from pathlib import Path

# MEDIA root
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MEDIA_ROOT = BASE_DIR / ".." / "media"
STATIC_ROOT = BASE_DIR / ".." / "static"

DEBUG = False

ALLOWED_HOSTS = [
    "hackme.rded.nl",
]

DJANGO_HOST = "hackme.rded.nl"
DOCKER_HOST = "hackme.rded.nl"

CONTAINER_NAMESPACE = "eu.gcr.io/hacking-in-c"
PROXY_CONTAINER = f"{CONTAINER_NAMESPACE}/exam-proxy"

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

ADMINS = [("Name", "Email")]

assert "SECRET_KEY" in os.environ

from .students import VALID_STUDENT_NUMBERS

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
SERVER_EMAIL = "noreply@hackme.rded.nl"
DEFAULT_FROM_EMAIL = "noreply@hackme.rded.nl"

EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "apikey"  # this is exactly the value 'apikey'
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True

DATABASES = {
    "default": {"ENGINE": "django.db.backends.postgresql", "NAME": "django",},
}

if "SENTRY_DSN" in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        send_default_pii=True,
    )
