from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max, Min, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from suplementos.forms import ProdutoForm
from suplementos.models import Categoria, Local, Produto


class ProdutoListView(ListView):
    model = Produto
    template_name = 'suplementos/pages/produtos.html'
    context_object_name = 'produtos'
    paginate_by = 40

    def get_queryset(self):
        qs = Produto.objects.select_related('categoria', 'local')

        q = self.request.GET.get('q', '').strip()
        if q:
            for termo in q.split():
                qs = qs.filter(
                    Q(nome_produto__icontains=termo)
                    | Q(marca__icontains=termo)
                    | Q(variacao__icontains=termo)
                )

        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)

        local_id = self.request.GET.get('local')
        if local_id:
            qs = qs.filter(local_id=local_id)

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        if self.request.GET.get('vencendo'):
            limite = timezone.localdate() + timedelta(days=60)
            qs = qs.filter(validade__isnull=False, validade__lte=limite)

        return qs.order_by('nome_produto')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categorias'] = Categoria.objects.all()
        ctx['locais'] = Local.objects.all()
        ctx['filtros'] = self.request.GET
        return ctx


class ProdutoCreateView(CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'suplementos/pages/produto_form.html'
    success_url = reverse_lazy('produtos')

    def form_valid(self, form):
        messages.success(self.request, 'Produto cadastrado com sucesso.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['margens_por_categoria'] = {
            c.id: str(c.margem_padrao_percentual) for c in Categoria.objects.all()
        }
        return ctx


class ProdutoUpdateView(UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'suplementos/pages/produto_form.html'
    success_url = reverse_lazy('produtos')

    def form_valid(self, form):
        messages.success(self.request, 'Produto atualizado com sucesso.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['margens_por_categoria'] = {
            c.id: str(c.margem_padrao_percentual) for c in Categoria.objects.all()
        }
        return ctx


class ProdutoDeleteView(DeleteView):
    model = Produto
    template_name = 'suplementos/pages/produto_confirm_delete.html'
    success_url = reverse_lazy('produtos')

    def form_valid(self, form):
        messages.success(self.request, 'Produto removido.')
        return super().form_valid(form)


@login_required
def comparar_precos(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    produtos = Produto.objects.filter(categoria=categoria).select_related('local').order_by('marca', 'p_venda')

    resumo = produtos.aggregate(menor=Min('p_venda'), medio=Avg('p_venda'), maior=Max('p_venda'))

    marcas = {}
    for p in produtos:
        marcas.setdefault(p.marca or 'Sem marca', []).append(p)

    return render(request, 'suplementos/pages/comparar_precos.html', {
        'categoria': categoria,
        'marcas': marcas,
        'resumo': resumo,
        'categorias': Categoria.objects.all(),
    })
