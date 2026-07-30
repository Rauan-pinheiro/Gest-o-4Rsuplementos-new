from suplementos.models import Produto


def produtos_para_seletor():
    """Lista enxuta de produtos em estoque, usada pelo componente JS de busca
    reutilizado em Vendas e Orçamento (seletor-produto.js)."""
    produtos = (
        Produto.objects.select_related('categoria', 'local')
        .filter(quantidade__gt=0)
        .order_by('nome_produto')
    )
    dados = []
    for p in produtos:
        rotulo = p.nome_produto
        if p.marca:
            rotulo += f" ({p.marca})"
        if p.variacao:
            rotulo += f" — {p.variacao}"
        if p.local:
            rotulo += f" [{p.local.nome_local}]"
        dados.append({
            'id': p.id,
            'rotulo': rotulo,
            'preco': str(p.p_venda),
            'custo': str(p.p_compra),
            'estoque': p.quantidade,
        })
    return dados
