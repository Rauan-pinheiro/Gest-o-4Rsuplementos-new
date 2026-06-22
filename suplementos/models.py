from django.db import models

# Create your models here.

from django.db import models

class Local(models.Model):
    nome_local = models.CharField(max_length=50, unique=True, verbose_name='Nome do local')
    
    def __str__(self):
        return self.nome_local
    
    class Meta:
        verbose_name = "Local de Armazenamento"
        verbose_name_plural = "Locais de Armazenamento"

class Produto(models.Model):
    # Opções para o campo Status
    STATUS_CHOICES = [
        ('OK', 'Ok'),
        ('BAIXO', 'Baixo'),
        ('ESGOTADO', 'Esgotado'),
    ]

    nome_produto = models.CharField(max_length=255, verbose_name="Nome do Produto")
    marca = models.CharField(max_length=100, verbose_name="Marca")
    variacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Variação (Sabor/Tamanho)")
    local = models.CharField(max_length=100, blank=True, null=True, verbose_name="Local de Armazenamento")
    quantidade = models.IntegerField(default=0, verbose_name="Quantidade")
    
    # Campos monetários (preços) recomendam DecimalField por precisão
    p_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Compra")
    p_venda = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Venda")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OK', verbose_name="Status")

    local = models.ForeignKey(
        Local,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produtos',
        verbose_name='Local de Armazenamento'
    )
    
    # Propriedade para calcular a margem de lucro automaticamente (Venda - Compra)
    @property
    def margem(self):
        return self.p_venda - self.p_compra

    # Exibe o nome do produto ao listar no painel Admin
    def __str__(self):
        return f"{self.nome_produto} ({self.marca})"

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
