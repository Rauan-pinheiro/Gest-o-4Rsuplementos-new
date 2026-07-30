from django.db import transaction

from suplementos.models import Venda, VendaItem


@transaction.atomic
def registrar_venda(*, cliente, local, forma_pagamento, data, itens, observacoes=""):
    """Cria uma Venda com seus itens e decrementa o estoque dos produtos vendidos.

    `itens` é uma lista de dicts: {"produto": Produto, "quantidade": int, "preco_unit_venda": Decimal (opcional)}.
    Só é chamada pela view de lançamento de venda — o import de dados legados
    cria Venda/VendaItem direto via ORM para não decrementar estoque que já
    reflete o pós-venda nos backups.
    """
    pago = forma_pagamento != 'FIADO'

    venda = Venda.objects.create(
        cliente=cliente,
        local=local,
        forma_pagamento=forma_pagamento,
        data=data,
        pago=pago,
        observacoes=observacoes,
    )

    for item in itens:
        produto = item['produto']
        quantidade = item['quantidade']
        preco_unit_venda = item.get('preco_unit_venda', produto.p_venda)

        VendaItem.objects.create(
            venda=venda,
            produto=produto,
            nome_produto_snapshot=str(produto),
            quantidade=quantidade,
            preco_unit_venda=preco_unit_venda,
            preco_unit_custo=produto.p_compra,
        )

        produto.quantidade -= quantidade
        produto.save()

    return venda


def marcar_como_pago(venda, data_pagamento=None):
    from django.utils import timezone

    venda.pago = True
    venda.data_pagamento = data_pagamento or timezone.localdate()
    venda.save(update_fields=['pago', 'data_pagamento'])
    return venda
