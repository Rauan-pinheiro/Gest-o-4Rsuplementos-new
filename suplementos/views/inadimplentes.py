from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from suplementos.models import Venda
from suplementos.services.vendas import marcar_como_pago


class InadimplentesListView(ListView):
    model = Venda
    template_name = 'suplementos/pages/inadimplentes.html'
    context_object_name = 'vendas'

    def get_queryset(self):
        return (
            Venda.objects.filter(forma_pagamento='FIADO', pago=False)
            .select_related('cliente', 'local')
            .prefetch_related('itens')
            .order_by('data')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_em_aberto'] = sum((v.total for v in ctx['vendas']), start=0)
        return ctx


@login_required
def marcar_pago(request, pk):
    venda = get_object_or_404(Venda, pk=pk, forma_pagamento='FIADO')
    if request.method == 'POST':
        marcar_como_pago(venda)
        messages.success(request, f'Venda #{venda.pk} de {venda.cliente.nome} marcada como paga.')
    return redirect('inadimplentes')
