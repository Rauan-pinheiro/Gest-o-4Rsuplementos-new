from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView

from suplementos.forms import PromocaoForm
from suplementos.models import Produto, Promocao, VendaItem


def _produtos_a_vencer(dias=60):
    limite = timezone.localdate() + timedelta(days=dias)
    return (
        Produto.objects.filter(validade__isnull=False, validade__lte=limite, quantidade__gt=0)
        .select_related('categoria', 'local')
        .order_by('validade')
    )


def _candidatos_a_desconto():
    """Produtos parados: estoque bem acima do mínimo, sem saída registrada recentemente."""
    return (
        Produto.objects.filter(quantidade__gt=0, quantidade_minima__gt=0)
        .select_related('categoria', 'local')
        .filter(quantidade__gte=3)
        .order_by('-quantidade')[:15]
    )


def _sugestoes_combo():
    """Combina produtos a vencer com os mais vendidos de outra categoria, como sugestão simples de combo."""
    mais_vendidos = (
        VendaItem.objects.filter(produto__isnull=False)
        .values('produto')
        .annotate(total_vendido=Sum('quantidade'))
        .order_by('-total_vendido')[:10]
    )
    ids_mais_vendidos = [item['produto'] for item in mais_vendidos]
    produtos_mais_vendidos = {p.id: p for p in Produto.objects.filter(id__in=ids_mais_vendidos)}

    sugestoes = []
    for produto_vencendo in _produtos_a_vencer(dias=45)[:8]:
        parceiro = next(
            (
                produtos_mais_vendidos[pid] for pid in ids_mais_vendidos
                if pid in produtos_mais_vendidos and produtos_mais_vendidos[pid].categoria_id != produto_vencendo.categoria_id
            ),
            None,
        )
        if parceiro:
            preco_combo = (produto_vencendo.p_venda + parceiro.p_venda) * Decimal('0.85')
            sugestoes.append({
                'produto_vencendo': produto_vencendo,
                'parceiro': parceiro,
                'preco_combo_sugerido': preco_combo.quantize(Decimal('0.01')),
            })
    return sugestoes


def _contexto_promocoes(form=None):
    return {
        'promocoes': Promocao.objects.prefetch_related('produtos').order_by('-ativo', '-data_inicio'),
        'produtos_a_vencer': _produtos_a_vencer()[:20],
        'candidatos_desconto': _candidatos_a_desconto(),
        'sugestoes_combo': _sugestoes_combo(),
        'form': form or PromocaoForm(),
    }


@login_required
def promocoes_view(request):
    return render(request, 'suplementos/pages/promocoes.html', _contexto_promocoes())


class PromocaoCreateView(CreateView):
    model = Promocao
    form_class = PromocaoForm
    template_name = 'suplementos/pages/promocoes.html'
    success_url = reverse_lazy('promocoes')

    def form_valid(self, form):
        messages.success(self.request, 'Promoção criada com sucesso.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Verifique os dados da promoção.')
        return render(self.request, self.template_name, _contexto_promocoes(form))


@login_required
def promocao_excluir(request, pk):
    promocao = get_object_or_404(Promocao, pk=pk)
    if request.method == 'POST':
        promocao.delete()
        messages.success(request, 'Promoção removida.')
    return redirect('promocoes')
