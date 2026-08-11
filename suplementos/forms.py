from django import forms

from .models import Categoria, ItemOrcamento, Orcamento, Produto, Promocao, Venda, VendaItem


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'nome_produto', 'marca', 'variacao', 'categoria', 'local',
            'quantidade', 'quantidade_minima', 'p_compra', 'p_venda', 'validade', 'obs',
        ]
        widgets = {
            'validade': forms.DateInput(attrs={'type': 'date'}),
            'obs': forms.Textarea(attrs={'rows': 3}),
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'margem_padrao_percentual']


class PromocaoForm(forms.ModelForm):
    class Meta:
        model = Promocao
        fields = [
            'tipo', 'nome', 'produtos', 'percentual_desconto', 'preco_fechado',
            'data_inicio', 'data_fim', 'ativo', 'observacoes',
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'produtos': forms.SelectMultiple(attrs={'size': 10}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }
