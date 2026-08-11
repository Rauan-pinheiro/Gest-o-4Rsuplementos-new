"""
Django settings for config project (4R Suplementos).
"""

from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)


# Security

SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[])

# Railway injeta automaticamente o domínio público do serviço (quando exposto)
# nessa variável. Adicionamos aqui além do que vier de DJANGO_ALLOWED_HOSTS /
# DJANGO_CSRF_TRUSTED_ORIGINS para não depender de configurar isso manualmente
# a cada novo domínio *.up.railway.app gerado no deploy.
RAILWAY_PUBLIC_DOMAIN = env('RAILWAY_PUBLIC_DOMAIN', default=None)
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS.append(RAILWAY_PUBLIC_DOMAIN)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RAILWAY_PUBLIC_DOMAIN}')

if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Começa conservador (1h) para não travar acesso caso o HTTPS tenha algum
    # problema no primeiro deploy; aumente via DJANGO_SECURE_HSTS_SECONDS
    # depois de confirmar que o site funciona 100% em HTTPS.
    SECURE_HSTS_SECONDS = env.int('DJANGO_SECURE_HSTS_SECONDS', default=3600)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # meus apps
    'suplementos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'suplementos.middleware.RequireLoginMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
#
# Railway (e outras PaaS) provisionam Postgres e injetam a URL completa em
# DATABASE_URL. Em VPS/docker-compose local não existe essa variável, e
# usamos as POSTGRES_* discretas (comportamento original, preservado).
DATABASE_URL = env('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {'default': env.db_url_config(DATABASE_URL)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('POSTGRES_DB'),
            'USER': env('POSTGRES_USER'),
            'PASSWORD': env('POSTGRES_PASSWORD'),
            'HOST': env('POSTGRES_HOST', default='db'),
            'PORT': env('POSTGRES_PORT', default='5432'),
        }
    }

DATABASES['default']['CONN_MAX_AGE'] = env.int('DJANGO_DB_CONN_MAX_AGE', default=60)


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# Static / media files

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

# Sem STORAGES['default']: o projeto não tem nenhum FileField/ImageField (a
# única foto — imagem de produto — foi removida), então não há upload de
# mídia de usuário. Mantemos só o backend de estáticos (WhiteNoise).
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Autenticação — sistema privado, login único

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'


# Logging — em produção (Railway/Docker) os logs vão para stdout/stderr, que
# a plataforma já coleta e disponibiliza. Não é preciso escrever em arquivo.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': env('DJANGO_LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
