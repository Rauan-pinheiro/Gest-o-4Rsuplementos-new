from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.urls import path, include


def healthz(request):
    """Healthcheck simples para a Railway (e outros orquestradores) — sem
    autenticação, sem tocar no banco, só confirma que o processo responde."""
    return HttpResponse('ok')


urlpatterns = [
    path('admin/', admin.site.urls),

    path('healthz/', healthz, name='healthz'),

    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', include('suplementos.urls')),
]
