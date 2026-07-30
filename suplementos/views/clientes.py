from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from suplementos.models import Cliente


@login_required
def cliente_detalhe(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    vendas = cliente.vendas.prefetch_related('itens').order_by('-data')
    total_gasto = sum((v.total for v in vendas), start=0)
    em_aberto = sum((v.total for v in vendas if not v.pago), start=0)

    return render(request, 'suplementos/pages/cliente_detalhe.html', {
        'cliente': cliente,
        'vendas': vendas,
        'total_gasto': total_gasto,
        'em_aberto': em_aberto,
    })
