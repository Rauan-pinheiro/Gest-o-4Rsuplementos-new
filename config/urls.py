from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.static import serve as static_serve

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', include('suplementos.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Fora do DEBUG o Django não serve MEDIA_URL sozinho. Como todo o site já
    # exige login via RequireLoginMiddleware, servir aqui mantém as imagens
    # de produto protegidas sem precisar de um serviço adicional (nginx).
    urlpatterns += [
        path('media/<path:path>', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ]
