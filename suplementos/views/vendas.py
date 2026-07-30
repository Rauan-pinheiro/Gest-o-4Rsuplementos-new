import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from suplementos.models import Cliente, Local, Produto, Venda
from suplementos.services.vendas import registrar_venda

from ._shared import produtos_para_seletor


def _parse_data(valor):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return timezone.localdate()


def _parse_decimal(valor, default):
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError):
        return default


@login_required
def venda_nova(request):
    if request.method == 'POST':
        cliente_nome = request.POST.get('cliente_nome', '').strip().upper()
        local_id = request.POST.get('local')
        forma_pagamento = request.POST.get('forma_pagamento', 'DINHEIRO')
        data_venda = _parse_data(request.POST.get('data'))
        observacoes = request.POST.get('observacoes', '').strip()

        try:
            itens_raw = json.loads(request.POST.get('itens_json', '[]'))
        except json.JSONDecodeError:
            itens_raw = []

        if not cliente_nome:
            messages.error(request, 'Informe o nome do cliente.')
        elif not itens_raw:
            messages.error(request, 'Adicione ao menos um produto à venda.')
        else:
            local = Local.objects.filter(pk=local_id).first() if local_id else None

            itens = []
            erro = False
            for item in itens_raw:
                produto = Produto.objects.filter(pk=item.get('produto_id')).first()
                if not produto:
                    continue
                quantidade = max(int(item.get('quantidade') or 1), 1)
                if quantidade > produto.quantidade:
                    messages.error(
                        request,
                        f'Estoque insuficiente para "{produto}". Disponível: {produto.quantidade}.'
                    )
                    erro = True
                    break
                preco = _parse_decimal(item.get('preco_unit_venda'), produto.p_venda)
                itens.append({'produto': produto, 'quantidade': quantidade, 'preco_unit_venda': preco})

            if not erro and itens:
                cliente, _ = Cliente.objects.get_or_create(nome=cliente_nome)
                venda = registrar_venda(
                    cliente=cliente, local=local, forma_pagamento=forma_pagamento,
                    data=data_venda, itens=itens, observacoes=observacoes,
                )
                messages.success(request, f'Venda #{venda.pk} registrada com sucesso.')
                return redirect('vendas')
            elif not erro:
                messages.error(request, 'Nenhum produto válido foi encontrado nesta venda.')

    context = {
        'produtos_json': produtos_para_seletor(),
        'clientes': Cliente.objects.order_by('nome'),
        'locais': Local.objects.all(),
        'forma_pagamento_choices': Venda.FORMA_PAGAMENTO_CHOICES,
        'hoje': timezone.localdate().isoformat(),
    }
    return render(request, 'suplementos/pages/vendas.html', context)
