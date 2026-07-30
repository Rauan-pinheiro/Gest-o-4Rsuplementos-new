import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView

from suplementos.models import Cliente, ItemOrcamento, Local, Orcamento, Produto
from suplementos.services.vendas import registrar_venda

from ._shared import produtos_para_seletor


def _parse_data(valor, default=None):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return default or timezone.localdate()


def _parse_decimal(valor, default):
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError):
        return default


@login_required
def orcamento_novo(request):
    if request.method == 'POST':
        cliente_nome = request.POST.get('cliente_nome', '').strip()
        validade = _parse_data(request.POST.get('validade_orcamento'), timezone.localdate() + timedelta(days=15))
        observacoes = request.POST.get('observacoes', '').strip()

        try:
            itens_raw = json.loads(request.POST.get('itens_json', '[]'))
        except json.JSONDecodeError:
            itens_raw = []

        if not itens_raw:
            messages.error(request, 'Adicione ao menos um produto ao orçamento.')
        else:
            cliente = None
            if cliente_nome:
                cliente, _ = Cliente.objects.get_or_create(nome=cliente_nome.strip().upper())

            orcamento = Orcamento.objects.create(
                cliente=cliente,
                cliente_nome_avulso='' if cliente else cliente_nome,
                validade_orcamento=validade,
                observacoes=observacoes,
            )
            for item in itens_raw:
                produto = Produto.objects.filter(pk=item.get('produto_id')).first()
                if not produto:
                    continue
                quantidade = max(int(item.get('quantidade') or 1), 1)
                preco = _parse_decimal(item.get('preco_unit_venda'), produto.p_venda)
                ItemOrcamento.objects.create(
                    orcamento=orcamento, produto=produto, nome_produto_snapshot=str(produto),
                    quantidade=quantidade, preco_unit_venda=preco,
                )

            messages.success(request, f'Orçamento #{orcamento.pk} gerado com sucesso.')
            return redirect('orcamento_detalhe', pk=orcamento.pk)

    context = {
        'produtos_json': produtos_para_seletor(),
        'clientes': Cliente.objects.order_by('nome'),
        'validade_padrao': (timezone.localdate() + timedelta(days=15)).isoformat(),
    }
    return render(request, 'suplementos/pages/orcamento.html', context)


class OrcamentoListView(ListView):
    model = Orcamento
    template_name = 'suplementos/pages/orcamento_lista.html'
    context_object_name = 'orcamentos'
    paginate_by = 30

    def get_queryset(self):
        return Orcamento.objects.select_related('cliente').prefetch_related('itens').order_by('-data', '-id')


@login_required
def orcamento_detalhe(request, pk):
    orcamento = get_object_or_404(
        Orcamento.objects.select_related('cliente', 'venda_gerada').prefetch_related('itens'), pk=pk
    )
    return render(request, 'suplementos/pages/orcamento_detalhe.html', {
        'orcamento': orcamento,
        'locais': Local.objects.all(),
    })


@login_required
def orcamento_converter(request, pk):
    orcamento = get_object_or_404(Orcamento, pk=pk)

    if request.method == 'POST' and orcamento.status == 'ABERTO':
        local_id = request.POST.get('local')
        forma_pagamento = request.POST.get('forma_pagamento', 'DINHEIRO')
        local = Local.objects.filter(pk=local_id).first() if local_id else None

        cliente = orcamento.cliente
        if not cliente:
            cliente, _ = Cliente.objects.get_or_create(nome=(orcamento.cliente_nome_avulso or 'CLIENTE NÃO IDENTIFICADO').upper())

        itens = []
        estoque_insuficiente = []
        for item in orcamento.itens.select_related('produto').all():
            if not item.produto:
                continue
            if item.quantidade > item.produto.quantidade:
                estoque_insuficiente.append(item.produto)
                continue
            itens.append({
                'produto': item.produto,
                'quantidade': item.quantidade,
                'preco_unit_venda': item.preco_unit_venda,
            })

        if estoque_insuficiente:
            nomes = ', '.join(str(p) for p in estoque_insuficiente)
            messages.error(request, f'Estoque insuficiente para converter: {nomes}.')
        elif not itens:
            messages.error(request, 'Este orçamento não tem itens com produto vinculado ao estoque.')
        else:
            venda = registrar_venda(
                cliente=cliente, local=local, forma_pagamento=forma_pagamento,
                data=timezone.localdate(), itens=itens,
                observacoes=f'Gerada a partir do orçamento #{orcamento.pk}.',
            )
            orcamento.venda_gerada = venda
            orcamento.status = 'CONVERTIDO'
            orcamento.save(update_fields=['venda_gerada', 'status'])
            messages.success(request, f'Orçamento convertido na venda #{venda.pk}.')
            return redirect('venda_detalhe', pk=venda.pk)

    return redirect('orcamento_detalhe', pk=orcamento.pk)
