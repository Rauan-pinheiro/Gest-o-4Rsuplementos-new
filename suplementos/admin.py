from django.contrib import admin
from . import models


@admin.register(models.Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('nome_local',)


@admin.register(models.Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'margem_padrao_percentual')
    search_fields = ('nome',)


@admin.register(models.Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        'nome_produto', 'marca', 'variacao', 'categoria', 'local',
        'quantidade', 'p_compra', 'p_venda', 'exibir_margem', 'status', 'validade',
    )
    list_filter = ('categoria', 'local', 'status', 'marca')
    search_fields = ('nome_produto', 'marca', 'variacao')

    def exibir_margem(self, obj):
        return f"{obj.margem_lucro:.0f}%"
    exibir_margem.short_description = 'Margem'


@admin.register(models.Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone')
    search_fields = ('nome',)


class VendaItemInline(admin.TabularInline):
    model = models.VendaItem
    extra = 0


@admin.register(models.Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'data', 'forma_pagamento', 'pago', 'local')
    list_filter = ('forma_pagamento', 'pago', 'local')
    search_fields = ('cliente__nome', 'observacoes')
    inlines = [VendaItemInline]


class ItemOrcamentoInline(admin.TabularInline):
    model = models.ItemOrcamento
    extra = 0


@admin.register(models.Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome_cliente', 'data', 'validade_orcamento', 'status')
    list_filter = ('status',)
    inlines = [ItemOrcamentoInline]


@admin.register(models.Promocao)
class PromocaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'data_inicio', 'data_fim', 'ativo', 'vigente')
    list_filter = ('tipo', 'ativo')
    filter_horizontal = ('produtos',)
