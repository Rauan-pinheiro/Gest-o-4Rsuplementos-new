from .dashboard import dashboard_view
from .produtos import (
    ProdutoCreateView,
    ProdutoDeleteView,
    ProdutoListView,
    ProdutoUpdateView,
    comparar_precos,
)
from .vendas import venda_nova
from .historico import HistoricoListView, venda_detalhe
from .inadimplentes import InadimplentesListView, marcar_pago
from .orcamento import OrcamentoListView, orcamento_converter, orcamento_detalhe, orcamento_novo
from .promocoes import PromocaoCreateView, promocao_excluir, promocoes_view
from .validades import validades_view
from .clientes import cliente_detalhe

__all__ = [
    'dashboard_view',
    'ProdutoCreateView', 'ProdutoDeleteView', 'ProdutoListView', 'ProdutoUpdateView', 'comparar_precos',
    'venda_nova',
    'HistoricoListView', 'venda_detalhe',
    'InadimplentesListView', 'marcar_pago',
    'OrcamentoListView', 'orcamento_converter', 'orcamento_detalhe', 'orcamento_novo',
    'PromocaoCreateView', 'promocao_excluir', 'promocoes_view',
    'validades_view',
    'cliente_detalhe',
]
