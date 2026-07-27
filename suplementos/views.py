from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'suplementos/pages/dashboard.html')

def historico(request):
    return render(request, 'suplementos/pages/historico.html')

def inadimplentes(request):
    return render(request, 'suplementos/pages/inadimplentes.html')

def orcamento(request):
    return render(request, 'suplementos/pages/inadimplentes.html')

def produtos(request):
    return render(request, 'suplementos/pages/produtos.html')

def promocoes(request):
    return render(request, 'suplementos/pages/promocoes.html')

def validades(request):
    return render(request, 'suplementos/pages/promocoes.html')

def vendas(request):
    return render(request, 'suplementos/pages/promocoes.html')