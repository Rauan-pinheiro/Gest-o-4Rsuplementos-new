from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse

EXEMPT_PREFIXES = (
    settings.STATIC_URL,
)


class RequireLoginMiddleware:
    """Exige login em todo o site — é um sistema privado de uso interno."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        exempt = (
            path.startswith(reverse('login'))
            or path == reverse('healthz')
            or any(path.startswith('/' + prefix.lstrip('/')) for prefix in EXEMPT_PREFIXES)
        )

        if not exempt and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url=reverse('login'))

        return self.get_response(request)
