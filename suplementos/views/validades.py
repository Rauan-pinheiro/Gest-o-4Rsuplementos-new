from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from suplementos.models import Produto


@login_required
def validades_view(request):
    hoje = timezone.localdate()
    limite = hoje + timedelta(days=90)

    produtos = (
        Produto.objects.filter(validade__isnull=False, quantidade__gt=0)
        .select_related('categoria', 'local')
        .order_by('validade')
    )

    vencidos = [p for p in produtos if p.validade < hoje]
    proximos = [p for p in produtos if hoje <= p.validade <= limite]
    demais = [p for p in produtos if p.validade > limite]

    return render(request, 'suplementos/pages/validades.html', {
        'vencidos': vencidos,
        'proximos': proximos,
        'demais': demais,
        'hoje': hoje,
    })
