import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.getenv("HUB20_SECRET_KEY")

DEBUG = "HUB20_DEBUG" in os.environ


ALLOWED_HOSTS = os.getenv("HUB20_ALLOWED_HOSTS", ["*"])

# Application definition

DJANGO_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.admin",
]

THIRD_PARTY_APPS = [
    "allauth",
    "allauth.account",
    "channels",
    "djmoney",
    "django_pdb",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_auth",
    "rest_auth.registration",
    "invitations",
    "qr_code",
]

PROJECT_APPS = [
    "hub20.apps.blockchain",
    "hub20.apps.ethereum_money",
    "hub20.apps.raiden",
    "hub20.apps.core",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

APPEND_SLASH = False
ROOT_URLCONF = "hub20.api.urls"
ASGI_APPLICATION = "hub20.api.routing.application"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.getenv("HUB20_DATABASE_ENGINE"),
        "HOST": os.getenv("HUB20_DATABASE_HOST"),
        "PORT": os.getenv("HUB20_DATABASE_PORT", 5432),
        "NAME": os.getenv("HUB20_DATABASE_NAME"),
        "USER": os.getenv("HUB20_DATABASE_USER"),
        "PASSWORD": os.getenv("HUB20_DATABASE_PASSWORD"),
    }
}


# Channel Configurations
CHANNEL_LAYER_BACKEND = os.getenv(
    "HUB20_CHANNEL_LAYER_BACKEND", "channels_redis.core.RedisChannelLayer"
)
CHANNEL_LAYER_HOST = os.getenv("HUB20_CHANNEL_LAYER_HOST", "redis")
CHANNEL_LAYER_PORT = int(os.getenv("HUB20_CHANNEL_LAYER_PORT", 6379))
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": CHANNEL_LAYER_BACKEND,
        "CONFIG": {"hosts": [(CHANNEL_LAYER_HOST, CHANNEL_LAYER_PORT)],},
    },
}

# Caches
DEFAULT_CACHE_BACKEND = os.getenv(
    "HUB20_CACHE_BACKEND", "django.core.cache.backends.filebased.FileBasedCache"
)

DEFAULT_CACHE_LOCATION = os.getenv("HUB20_CACHE_URL", "/tmp/hub20_cache")

DEFAULT_CACHE_OPTIONS = {
    "django_redis.cache.RedisCache": {"CLIENT_CLASS": "django_redis.client.DefaultClient"}
}.get(DEFAULT_CACHE_BACKEND, {})


CACHES = {
    "default": {
        "BACKEND": DEFAULT_CACHE_BACKEND,
        "LOCATION": os.getenv("HUB20_CACHE_LOCATION", DEFAULT_CACHE_LOCATION),
        "OPTIONS": DEFAULT_CACHE_OPTIONS,
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Email
DEFAULT_FROM_EMAIL = os.getenv("HUB20_EMAIL_MAILER_ADDRESS")
EMAIL_BACKEND = os.getenv("HUB20_EMAIL_BACKEND")
EMAIL_HOST = os.getenv("HUB20_EMAIL_HOST")
EMAIL_PORT = os.getenv("HUB20_EMAIL_PORT")
EMAIL_HOST_USER = os.getenv("HUB20_EMAIL_SMTP_USERNAME")
EMAIL_HOST_PASSWORD = os.getenv("HUB20_EMAIL_SMTP_PASSWORD")
EMAIL_TIMEOUT = os.getenv("HUB20_EMAIL_TIMEOUT", 5)


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


SITE_ID = 1
HUB20_SITE_DOMAIN = os.getenv("HUB20_SITE_DOMAIN")

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STATIC_URL = "/static/"

ADMIN_USERNAME = os.getenv("HUB20_ADMIN_USERNAME", "admin")


# Configuration of authentication/signup/registration via django-allauth/invitations
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
INVITATIONS_ACCEPT_INVITE_AFTER_SIGNUP = True
INVITATIONS_SIGNUP_REDIRECT = "signup"
INVITATIONS_ADAPTER = ACCOUNT_ADAPTER = "invitations.models.InvitationsAdapter"
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_BLACKLIST = [
    "about",
    "access",
    "account",
    "accounts",
    "add",
    "address",
    "adm",
    "admin",
    "administration",
    "adult",
    "advertising",
    "affiliate",
    "affiliates",
    "ajax",
    "analytics",
    "android",
    "anon",
    "anonymous",
    "api",
    "app",
    "apps",
    "archive",
    "atom",
    "auth",
    "authentication",
    "avatar",
    "backup",
    "banner",
    "banners",
    "bin",
    "billing",
    "blog",
    "blogs",
    "board",
    "bot",
    "bots",
    "business",
    "chat",
    "cache",
    "cadastro",
    "calendar",
    "campaign",
    "careers",
    "cgi",
    "client",
    "cliente",
    "code",
    "comercial",
    "compare",
    "config",
    "connect",
    "contact",
    "contest",
    "create",
    "code",
    "compras",
    "css",
    "dashboard",
    "data",
    "db",
    "design",
    "delete",
    "demo",
    "design",
    "designer",
    "dev",
    "devel",
    "dir",
    "directory",
    "doc",
    "docs",
    "domain",
    "download",
    "downloads",
    "edit",
    "editor",
    "email",
    "ecommerce",
    "forum",
    "forums",
    "faq",
    "favorite",
    "feed",
    "feedback",
    "flog",
    "follow",
    "file",
    "files",
    "free",
    "ftp",
    "gadget",
    "gadgets",
    "games",
    "guest",
    "group",
    "groups",
    "help",
    "home",
    "homepage",
    "host",
    "hosting",
    "hostname",
    "html",
    "http",
    "httpd",
    "https",
    "hpg",
    "info",
    "information",
    "image",
    "img",
    "images",
    "imap",
    "index",
    "invite",
    "intranet",
    "indice",
    "ipad",
    "iphone",
    "irc",
    "java",
    "javascript",
    "job",
    "jobs",
    "js",
    "knowledgebase",
    "log",
    "login",
    "logs",
    "logout",
    "list",
    "lists",
    "mail",
    "mail1",
    "mail2",
    "mail3",
    "mail4",
    "mail5",
    "mailer",
    "mailing",
    "mx",
    "manager",
    "marketing",
    "master",
    "me",
    "media",
    "message",
    "microblog",
    "microblogs",
    "mine",
    "mp3",
    "msg",
    "msn",
    "mysql",
    "messenger",
    "mob",
    "mobile",
    "movie",
    "movies",
    "music",
    "musicas",
    "my",
    "name",
    "named",
    "net",
    "network",
    "new",
    "news",
    "newsletter",
    "nick",
    "nickname",
    "notes",
    "noticias",
    "ns",
    "ns1",
    "ns2",
    "ns3",
    "ns4",
    "old",
    "online",
    "operator",
    "order",
    "orders",
    "page",
    "pager",
    "pages",
    "panel",
    "password",
    "perl",
    "pic",
    "pics",
    "photo",
    "photos",
    "photoalbum",
    "php",
    "plugin",
    "plugins",
    "pop",
    "pop3",
    "post",
    "postmaster",
    "postfix",
    "posts",
    "profile",
    "project",
    "projects",
    "promo",
    "pub",
    "public",
    "python",
    "random",
    "register",
    "registration",
    "root",
    "ruby",
    "rss",
    "sale",
    "sales",
    "sample",
    "samples",
    "script",
    "scripts",
    "secure",
    "send",
    "service",
    "shop",
    "sql",
    "signup",
    "signin",
    "search",
    "security",
    "settings",
    "setting",
    "setup",
    "site",
    "sites",
    "sitemap",
    "smtp",
    "soporte",
    "ssh",
    "stage",
    "staging",
    "start",
    "subscribe",
    "subdomain",
    "suporte",
    "support",
    "stat",
    "static",
    "stats",
    "status",
    "store",
    "stores",
    "system",
    "tablet",
    "tablets",
    "tech",
    "telnet",
    "test",
    "test1",
    "test2",
    "test3",
    "teste",
    "tests",
    "theme",
    "themes",
    "tmp",
    "todo",
    "task",
    "tasks",
    "tools",
    "tv",
    "talk",
    "update",
    "upload",
    "url",
    "user",
    "username",
    "usuario",
    "usage",
    "vendas",
    "video",
    "videos",
    "visitor",
    "win",
    "ww",
    "www",
    "www1",
    "www2",
    "www3",
    "www4",
    "www5",
    "www6",
    "www7",
    "wwww",
    "wws",
    "wwws",
    "web",
    "webmail",
    "website",
    "websites",
    "webmaster",
    "workshop",
    "xxx",
    "xpg",
    "you",
    "yourname",
    "yourusername",
    "yoursite",
    "yourdomain",
]

# Web3 and Hub20 configuration
WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI", "http://localhost:8545")
ETHEREUM_ACCOUNT_MODEL = os.getenv(
    "HUB20_ETHEREUM_ACCOUNT_MODEL", "ethereum_money.EthereumAccount"
)

BLOCKCHAIN_START_BLOCK_NUMBER = os.getenv("HUB20_BLOCKCHAIN_STARTING_BLOCK")


# Logging Configuration
LOG_FILE = os.getenv("HUB20_SITE_LOG_FILE")
LOG_LEVEL = os.getenv("HUB20_LOG_LEVEL", "DEBUG" if DEBUG else "INFO")
LOGGING = {
    "version": 1,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s:%(pathname)s %(process)d %(lineno)d %(message)s"
        },
        "simple": {"format": "%(levelname)s:%(module)s %(lineno)d %(message)s"},
    },
    "handlers": {
        "null": {"level": "DEBUG", "class": "logging.NullHandler"},
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "filename": LOG_FILE,
            "maxBytes": 16 * 1024 * 1024,
            "backupCount": 3,
        },
    },
    "loggers": {
        "django": {"handlers": ["null"], "propagate": True, "level": "INFO"},
        "django.db.backends:": {"handlers": ["file"], "level": "ERROR", "propagate": False},
        "django.request": {"handlers": ["file"], "level": "ERROR", "propagate": False},
    },
}


for app in PROJECT_APPS:
    LOGGING["loggers"][app] = {
        "handlers": ["console", "file"],
        "level": "DEBUG" if DEBUG else "INFO",
        "propagate": False,
    }
