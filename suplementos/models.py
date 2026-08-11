from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.utils import timezone


class Local(models.Model):
    nome_local = models.CharField(max_length=50, unique=True, verbose_name='Nome do local')

    def __str__(self):
        return self.nome_local

    class Meta:
        verbose_name = "Local de Armazenamento"
        verbose_name_plural = "Locais de Armazenamento"
        ordering = ['nome_local']


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Categoria")
    margem_padrao_percentual = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('60.00'),
        verbose_name="Margem padrão sugerida (%)",
        help_text="Usada para sugerir o preço de venda ao cadastrar um produto desta categoria."
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['nome']


class Produto(models.Model):
    STATUS_CHOICES = [
        ('OK', 'Ok'),
        ('BAIXO', 'Baixo'),
        ('ESGOTADO', 'Esgotado'),
    ]

    nome_produto = models.CharField(max_length=255, verbose_name="Nome do Produto")
    marca = models.CharField(max_length=100, blank=True, verbose_name="Marca")
    variacao = models.CharField(max_length=100, blank=True, verbose_name="Variação (Sabor/Tamanho)")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='produtos', verbose_name='Categoria'
    )
    local = models.ForeignKey(
        Local, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='produtos', verbose_name='Local de Armazenamento'
    )

    quantidade = models.IntegerField(default=0, verbose_name="Quantidade")
    quantidade_minima = models.IntegerField(default=1, verbose_name="Quantidade mínima (alerta de estoque baixo)")

    p_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Compra")
    p_venda = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço de Venda")

    validade = models.DateField(null=True, blank=True, verbose_name="Data de validade")
    obs = models.TextField(blank=True, verbose_name="Observações")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OK', verbose_name="Status")

    legacy_id = models.CharField(max_length=64, unique=True, null=True, blank=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    @property
    def margem_lucro(self):
        if not self.p_compra:
            return Decimal('0')
        return ((self.p_venda - self.p_compra) / self.p_compra) * 100

    @property
    def preco_sugerido(self):
        if not self.categoria or self.p_compra is None:
            return None
        margem = self.categoria.margem_padrao_percentual / Decimal('100')
        return (self.p_compra * (1 + margem)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def atualizar_status(self):
        if self.quantidade <= 0:
            self.status = 'ESGOTADO'
        elif self.quantidade <= self.quantidade_minima:
            self.status = 'BAIXO'
        else:
            self.status = 'OK'

    def save(self, *args, **kwargs):
        self.atualizar_status()
        super().save(*args, **kwargs)

    def __str__(self):
        partes = [self.nome_produto]
        if self.marca:
            partes.append(f"({self.marca})")
        return " ".join(partes)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['nome_produto']


class Cliente(models.Model):
    nome = models.CharField(max_length=255, unique=True, verbose_name="Nome")
    telefone = models.CharField(max_length=30, blank=True, verbose_name="Telefone")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']


class Venda(models.Model):
    FORMA_PAGAMENTO_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('PIX', 'Pix'),
        ('CARTAO', 'Cartão'),
        ('FIADO', 'Fiado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='vendas', verbose_name="Cliente")
    local = models.ForeignKey(
        Local, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='vendas', verbose_name='Local'
    )
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_PAGAMENTO_CHOICES, default='DINHEIRO')
    data = models.DateField(default=timezone.localdate, verbose_name="Data da venda")

    pago = models.BooleanField(default=True, verbose_name="Pago")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data do pagamento")

    observacoes = models.TextField(blank=True, verbose_name="Observações")

    legacy_id = models.CharField(max_length=64, unique=True, null=True, blank=True, db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return sum((item.subtotal_venda for item in self.itens.all()), Decimal('0'))

    @property
    def custo_total(self):
        return sum((item.subtotal_custo for item in self.itens.all()), Decimal('0'))

    @property
    def lucro(self):
        return self.total - self.custo_total

    def __str__(self):
        return f"Venda #{self.pk} — {self.cliente.nome} ({self.data})"

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ['-data', '-id']


class VendaItem(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(
        Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_venda'
    )
    nome_produto_snapshot = models.CharField(max_length=255)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unit_venda = models.DecimalField(max_digits=10, decimal_places=2)
    preco_unit_custo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))

    @property
    def subtotal_venda(self):
        return self.preco_unit_venda * self.quantidade

    @property
    def subtotal_custo(self):
        return self.preco_unit_custo * self.quantidade

    def __str__(self):
        return f"{self.quantidade}x {self.nome_produto_snapshot}"

    class Meta:
        verbose_name = "Item de Venda"
        verbose_name_plural = "Itens de Venda"


class Orcamento(models.Model):
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('CONVERTIDO', 'Convertido em venda'),
        ('EXPIRADO', 'Expirado'),
    ]

    cliente = models.ForeignKey(
        Cliente, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orcamentos', verbose_name="Cliente"
    )
    cliente_nome_avulso = models.CharField(max_length=255, blank=True, verbose_name="Nome do cliente (avulso)")

    data = models.DateField(default=timezone.localdate, verbose_name="Data do orçamento")
    validade_orcamento = models.DateField(null=True, blank=True, verbose_name="Válido até")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')

    venda_gerada = models.OneToOneField(
        Venda, on_delete=models.SET_NULL, null=True, blank=True, related_name='orcamento_origem'
    )
    observacoes = models.TextField(blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    @property
    def nome_cliente(self):
        return self.cliente.nome if self.cliente else self.cliente_nome_avulso

    @property
    def total(self):
        return sum((item.subtotal_venda for item in self.itens.all()), Decimal('0'))

    def __str__(self):
        return f"Orçamento #{self.pk} — {self.nome_cliente}"

    class Meta:
        verbose_name = "Orçamento"
        verbose_name_plural = "Orçamentos"
        ordering = ['-data', '-id']


class ItemOrcamento(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='itens')
    produto = models.ForeignKey(
        Produto, on_delete=models.SET_NULL, null=True, blank=True, related_name='itens_orcamento'
    )
    nome_produto_snapshot = models.CharField(max_length=255)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unit_venda = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal_venda(self):
        return self.preco_unit_venda * self.quantidade

    def __str__(self):
        return f"{self.quantidade}x {self.nome_produto_snapshot}"

    class Meta:
        verbose_name = "Item de Orçamento"
        verbose_name_plural = "Itens de Orçamento"


class Promocao(models.Model):
    TIPO_CHOICES = [
        ('DESCONTO', 'Desconto'),
        ('COMBO', 'Combo'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='DESCONTO')
    nome = models.CharField(max_length=255, verbose_name="Nome da promoção")
    produtos = models.ManyToManyField(Produto, related_name='promocoes', blank=True)

    percentual_desconto = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Usado quando o tipo é Desconto."
    )
    preco_fechado = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Preço fechado do combo (soma de todos os produtos incluídos)."
    )

    data_inicio = models.DateField(default=timezone.localdate)
    data_fim = models.DateField()
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)

    @property
    def vigente(self):
        hoje = timezone.localdate()
        return self.ativo and self.data_inicio <= hoje <= self.data_fim

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Promoção"
        verbose_name_plural = "Promoções"
        ordering = ['-data_inicio']
