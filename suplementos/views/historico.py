from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView

from suplementos.models import Cliente, Venda


class HistoricoListView(ListView):
    model = Venda
    template_name = 'suplementos/pages/historico.html'
    context_object_name = 'vendas'
    paginate_by = 40

    def get_queryset(self):
        qs = Venda.objects.select_related('cliente', 'local').prefetch_related('itens')

        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)

        forma_pagamento = self.request.GET.get('forma_pagamento')
        if forma_pagamento:
            qs = qs.filter(forma_pagamento=forma_pagamento)

        data_inicio = self.request.GET.get('data_inicio')
        if data_inicio:
            qs = qs.filter(data__gte=data_inicio)

        data_fim = self.request.GET.get('data_fim')
        if data_fim:
            qs = qs.filter(data__lte=data_fim)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['clientes'] = Cliente.objects.order_by('nome')
        ctx['forma_pagamento_choices'] = Venda.FORMA_PAGAMENTO_CHOICES
        ctx['filtros'] = self.request.GET
        return ctx


@login_required
def venda_detalhe(request, pk):
    venda = get_object_or_404(Venda.objects.select_related('cliente', 'local').prefetch_related('itens'), pk=pk)
    return render(request, 'suplementos/pages/venda_detalhe.html', {'venda': venda})
