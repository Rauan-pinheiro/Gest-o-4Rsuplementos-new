from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),

    path('produtos/', views.ProdutoListView.as_view(), name='produtos'),
    path('produtos/novo/', views.ProdutoCreateView.as_view(), name='produto_novo'),
    path('produtos/<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='produto_editar'),
    path('produtos/<int:pk>/excluir/', views.ProdutoDeleteView.as_view(), name='produto_excluir'),
    path('produtos/comparar/<int:categoria_id>/', views.comparar_precos, name='produtos_comparar'),

    path('vendas/', views.venda_nova, name='vendas'),

    path('historico/', views.HistoricoListView.as_view(), name='historico'),
    path('historico/<int:pk>/', views.venda_detalhe, name='venda_detalhe'),

    path('inadimplentes/', views.InadimplentesListView.as_view(), name='inadimplentes'),
    path('inadimplentes/<int:pk>/pagar/', views.marcar_pago, name='inadimplente_pagar'),

    path('orcamento/', views.orcamento_novo, name='orcamento'),
    path('orcamento/lista/', views.OrcamentoListView.as_view(), name='orcamento_lista'),
    path('orcamento/<int:pk>/', views.orcamento_detalhe, name='orcamento_detalhe'),
    path('orcamento/<int:pk>/converter/', views.orcamento_converter, name='orcamento_converter'),

    path('promocoes/', views.promocoes_view, name='promocoes'),
    path('promocoes/nova/', views.PromocaoCreateView.as_view(), name='promocao_nova'),
    path('promocoes/<int:pk>/excluir/', views.promocao_excluir, name='promocao_excluir'),

    path('validades/', views.validades_view, name='validades'),

    path('clientes/<int:pk>/', views.cliente_detalhe, name='cliente_detalhe'),
]
