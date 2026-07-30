import json
from datetime import date
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from suplementos.models import Categoria, Cliente, Local, Produto, Venda, VendaItem

LOCAL_NOMES = {
    'betania': 'Betânia',
    'baixio': 'Baixio',
    'shopep': 'Shopep',
    'loc4': 'Local 4',
    'loc5': 'Local 5',
}

# Corrige typos de nome de cliente encontrados entre os arquivos de backup
# (ex: o mesmo cliente grafado diferente em vendas.json e inadimplentes.json).
CLIENTE_ALIASES = {
    'LARISSA BETNAIA': 'LARISSA BETANIA',
}

FORMA_PAGAMENTO_MAP = {
    'dinheiro': 'DINHEIRO',
    'pix': 'PIX',
    'cartao': 'CARTAO',
    'cartão': 'CARTAO',
    'fiado': 'FIADO',
}

MARGEM_PADRAO_INICIAL = Decimal('60.00')


def _ler_json(nome_arquivo):
    caminho = settings.BASE_DIR / 'backups' / nome_arquivo
    with open(caminho, encoding='utf-8') as f:
        return json.load(f)


def _como_lista(valor):
    """Os backups às vezes guardam arrays como string JSON. Normaliza para lista."""
    if isinstance(valor, str):
        valor = valor.strip()
        return json.loads(valor) if valor else []
    return valor or []


def _parse_data(valor):
    if not valor:
        return None
    valor = str(valor).strip()
    if len(valor) < 4:
        return None
    ano_str = valor[:4]
    try:
        ano = int(ano_str)
    except ValueError:
        return None
    if ano < 2000:
        # corrige typo de digitação tipo "0026-07-29" -> "2026-07-29"
        valor = '20' + valor[2:]
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


def _decimal(valor, default='0'):
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError):
        return Decimal(default)


def _normalizar_nome(nome):
    nome = (nome or '').strip().upper()
    nome = ' '.join(nome.split())
    return CLIENTE_ALIASES.get(nome, nome) or 'CLIENTE NÃO IDENTIFICADO'


class Command(BaseCommand):
    help = "Importa produtos, vendas e inadimplentes dos backups legados em backups/*.json (idempotente)."

    def handle(self, *args, **options):
        self.locais = self._importar_locais()
        self.categorias = {}

        total_produtos = self._importar_produtos()
        total_clientes_antes = Cliente.objects.count()
        total_vendas, itens_sem_produto = self._importar_vendas()
        total_clientes = Cliente.objects.count()
        casados, orfaos = self._importar_inadimplentes()

        self.stdout.write(self.style.SUCCESS(
            "\nImportação concluída:\n"
            f"  Locais: {len(self.locais)}\n"
            f"  Categorias: {len(self.categorias)}\n"
            f"  Produtos: {total_produtos}\n"
            f"  Clientes: {total_clientes} (novos nesta execução: {total_clientes - total_clientes_antes})\n"
            f"  Vendas: {total_vendas} (itens sem produto casado: {itens_sem_produto})\n"
            f"  Inadimplentes casados com uma venda existente: {casados}\n"
            f"  Inadimplentes órfãos (venda avulsa criada): {orfaos}\n"
            "\nRevise manualmente no admin as margens padrão de cada categoria "
            f"(criadas com {MARGEM_PADRAO_INICIAL}% por padrão — os dados legados têm margens "
            "reais inconsistentes demais para servir de base automática)."
        ))

    # ------------------------------------------------------------------

    def _importar_locais(self):
        locais = {}
        for slug, nome in LOCAL_NOMES.items():
            local, _ = Local.objects.get_or_create(nome_local=nome)
            locais[slug] = local
        return locais

    def _get_categoria(self, nome_bruto):
        nome = (nome_bruto or 'SEM CATEGORIA').strip().upper() or 'SEM CATEGORIA'
        categoria = self.categorias.get(nome)
        if not categoria:
            categoria, _ = Categoria.objects.get_or_create(
                nome=nome,
                defaults={'margem_padrao_percentual': MARGEM_PADRAO_INICIAL},
            )
            self.categorias[nome] = categoria
        return categoria

    def _importar_produtos(self):
        dados = _ler_json('backup-produtos.json')
        produtos_raw = _como_lista(dados.get('4r2_products'))

        total = 0
        for p in produtos_raw:
            legacy_id = p.get('id')
            if not legacy_id:
                continue

            categoria = self._get_categoria(p.get('category'))
            local = self.locais.get(p.get('location'))

            Produto.objects.update_or_create(
                legacy_id=legacy_id,
                defaults={
                    'nome_produto': (p.get('name') or '').strip() or 'PRODUTO SEM NOME',
                    'marca': (p.get('brand') or '').strip(),
                    'variacao': (p.get('variation') or '').strip(),
                    'categoria': categoria,
                    'local': local,
                    'quantidade': int(p.get('qty') or 0),
                    'quantidade_minima': int(p.get('minQty') or 1),
                    'p_compra': _decimal(p.get('buyPrice')),
                    'p_venda': _decimal(p.get('sellPrice')),
                    'validade': _parse_data(p.get('expiry')),
                    'obs': p.get('obs') or '',
                },
            )
            total += 1
        return total

    def _resolver_produto(self, prod_id):
        if not prod_id:
            return None
        return Produto.objects.filter(legacy_id=prod_id).first()

    def _importar_vendas(self):
        dados = _ler_json('backup-vendas.json')
        vendas_raw = _como_lista(dados.get('4r2_sales'))

        total_vendas = 0
        itens_sem_produto = 0

        for v in vendas_raw:
            legacy_id = v.get('id')
            if not legacy_id:
                continue

            cliente, _ = Cliente.objects.get_or_create(nome=_normalizar_nome(v.get('client')))
            local = self.locais.get(v.get('location'))
            forma_pagamento = FORMA_PAGAMENTO_MAP.get((v.get('payment') or '').strip().lower(), 'DINHEIRO')
            data_venda = _parse_data(v.get('date')) or timezone.localdate()
            pago = forma_pagamento != 'FIADO'

            venda, _ = Venda.objects.update_or_create(
                legacy_id=legacy_id,
                defaults={
                    'cliente': cliente,
                    'local': local,
                    'forma_pagamento': forma_pagamento,
                    'data': data_venda,
                    'pago': pago,
                },
            )
            venda.itens.all().delete()

            for item in v.get('items', []):
                produto = self._resolver_produto(item.get('prodId'))
                if produto is None:
                    itens_sem_produto += 1

                VendaItem.objects.create(
                    venda=venda,
                    produto=produto,
                    nome_produto_snapshot=item.get('name') or (produto and str(produto)) or 'Produto',
                    quantidade=int(item.get('qty') or 1),
                    preco_unit_venda=_decimal(item.get('price')),
                    preco_unit_custo=_decimal(item.get('buyPrice')),
                )

            total_vendas += 1

        return total_vendas, itens_sem_produto

    def _importar_inadimplentes(self):
        dados = _ler_json('backup-inadimplentes.json')
        registros = _como_lista(dados.get('4r2_inadimplentes'))

        casados = 0
        orfaos = 0

        for r in registros:
            nome = _normalizar_nome(r.get('name'))
            valor = _decimal(r.get('value'))
            data_registro = _parse_data(r.get('date'))
            pago = bool(r.get('paid'))
            data_pagamento = _parse_data(r.get('paidDate'))

            candidatos = Venda.objects.filter(forma_pagamento='FIADO')
            if data_registro:
                candidatos = candidatos.filter(data=data_registro)

            melhor_venda = None
            melhor_score = 0.0
            for candidata in candidatos.select_related('cliente').prefetch_related('itens'):
                if abs(candidata.total - valor) > Decimal('0.01'):
                    continue
                score = SequenceMatcher(None, nome, candidata.cliente.nome).ratio()
                if score > melhor_score:
                    melhor_score = score
                    melhor_venda = candidata

            if melhor_venda and melhor_score >= 0.6:
                melhor_venda.pago = pago
                melhor_venda.data_pagamento = data_pagamento if pago else None
                melhor_venda.save(update_fields=['pago', 'data_pagamento'])
                casados += 1
            else:
                cliente, _ = Cliente.objects.get_or_create(nome=nome)
                descricao = r.get('products') or ''
                obs = r.get('obs') or ''
                Venda.objects.get_or_create(
                    legacy_id=f"inad-{r.get('id')}",
                    defaults={
                        'cliente': cliente,
                        'forma_pagamento': 'FIADO',
                        'data': data_registro or timezone.localdate(),
                        'pago': pago,
                        'data_pagamento': data_pagamento if pago else None,
                        'observacoes': (
                            f"Importado do backup de inadimplentes sem produto casado no estoque.\n"
                            f"Produtos (texto original): {descricao}\n"
                            f"Observação original: {obs}"
                        ).strip(),
                    },
                )
                orfaos += 1

        return casados, orfaos
