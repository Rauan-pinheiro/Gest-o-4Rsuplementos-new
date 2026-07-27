
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('historico/', views.historico, name='historico'),
    path('inadimplentes/', views.inadimplentes, name='inadimplentes'),
    path('orcamento/', views.orcamento, name='orcamento'),
    path('produtos/', views.produtos, name='produtos'),
    path('promocoes/', views.promocoes, name='promocoes'),
    path('validades/', views.validades, name='validades'),
    path('vendas/', views.vendas, name='vendas'),
]