from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from suplementos.models import Cliente, Produto, VendaItem

MESES_PT = [
    'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez',
]


def _grafico_mensal():
    hoje = timezone.localdate()
    inicio_janela = (hoje.replace(day=1) - timedelta(days=335)).replace(day=1)

    dados = (
        VendaItem.objects.filter(venda__data__gte=inicio_janela)
        .annotate(mes=TruncMonth('venda__data'))
        .values('mes')
        .annotate(total=Sum(F('preco_unit_venda') * F('quantidade')))
    )
    totais_por_mes = {item['mes']: item['total'] for item in dados}

    labels = []
    valores = []
    cursor = inicio_janela
    for _ in range(12):
        labels.append(f"{MESES_PT[cursor.month - 1]}/{str(cursor.year)[2:]}")
        valores.append(float(totais_por_mes.get(cursor, 0) or 0))
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)

    return labels, valores


@login_required
def dashboard_view(request):
    hoje = timezone.localdate()

    agregados = VendaItem.objects.aggregate(
        bruto=Sum(F('preco_unit_venda') * F('quantidade')),
        custo=Sum(F('preco_unit_custo') * F('quantidade')),
    )
    total_bruto = agregados['bruto'] or Decimal('0')
    total_custo = agregados['custo'] or Decimal('0')
    total_liquido = total_bruto - total_custo

    produtos_estoque_baixo = Produto.objects.filter(status__in=['BAIXO', 'ESGOTADO'])

    limite_validade = hoje + timedelta(days=60)
    produtos_vencendo = Produto.objects.filter(
        validade__isnull=False, validade__lte=limite_validade, quantidade__gt=0
    )

    mais_vendidos = (
        VendaItem.objects.filter(produto__isnull=False)
        .values('produto__id', 'produto__nome_produto', 'produto__marca')
        .annotate(total_vendido=Sum('quantidade'))
        .order_by('-total_vendido')[:8]
    )

    top_clientes = (
        Cliente.objects.annotate(
            gasto_total=Sum(F('vendas__itens__preco_unit_venda') * F('vendas__itens__quantidade'))
        )
        .filter(gasto_total__isnull=False)
        .order_by('-gasto_total')[:5]
    )

    labels_mensal, valores_mensal = _grafico_mensal()

    return render(request, 'suplementos/pages/dashboard.html', {
        'total_bruto': total_bruto,
        'total_liquido': total_liquido,
        'produtos_estoque_baixo': produtos_estoque_baixo,
        'produtos_vencendo': produtos_vencendo,
        'mais_vendidos': mais_vendidos,
        'top_clientes': top_clientes,
        'labels_mensal': labels_mensal,
        'valores_mensal': valores_mensal,
    })
