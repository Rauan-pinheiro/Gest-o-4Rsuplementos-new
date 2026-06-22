from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.Produto)
class ProdutoAdmin(admin.ModelAdmin):
    
    # Campos que vão aparecer na tabela de listagem do Admin
    list_display = ('nome_produto', 'marca', 'local', 'quantidade', 'p_compra', 'p_venda', 'exibir_margem', 'status')
    
    list_filter = ('marca', 'local', 'status')
    
    # Como margem é uma propriedade calculada, precisamos de uma função para exibir no admin
    def exibir_margem(self, obj):
        return f"R$ {obj.margem}"
    
    exibir_margem.short_description = 'Margem'
    
@admin.register(models.Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('nome_local',)