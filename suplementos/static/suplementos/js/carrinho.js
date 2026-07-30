/* Componente de seleção de produtos do estoque, reutilizado em Vendas e Orçamento.
 * Espera encontrar no DOM: #produto-busca, #produto-sugestoes, #carrinho-corpo,
 * #carrinho-total, #itens_json, #carrinho-form e um json_script #produtos-data.
 */
(function () {
    var dadosEl = document.getElementById('produtos-data');
    if (!dadosEl) return;

    var produtos = JSON.parse(dadosEl.textContent);
    var busca = document.getElementById('produto-busca');
    var sugestoesBox = document.getElementById('produto-sugestoes');
    var corpo = document.getElementById('carrinho-corpo');
    var totalEl = document.getElementById('carrinho-total');
    var itensInput = document.getElementById('itens_json');
    var form = document.getElementById('carrinho-form');

    var carrinho = [];

    function formatarMoeda(valor) {
        return 'R$ ' + valor.toFixed(2).replace('.', ',');
    }

    function atualizar() {
        corpo.innerHTML = '';
        var total = 0;

        carrinho.forEach(function (item, indice) {
            var subtotal = item.quantidade * item.preco_unit_venda;
            total += subtotal;

            var tr = document.createElement('tr');
            tr.innerHTML =
                '<td data-rotulo="Produto">' + item.rotulo + '</td>' +
                '<td data-rotulo="Qtd"><input type="number" min="1" max="' + item.estoque + '" value="' + item.quantidade + '" data-indice="' + indice + '" class="carrinho-qtd" style="width:80px"></td>' +
                '<td data-rotulo="Preço unit."><input type="number" min="0" step="0.01" value="' + item.preco_unit_venda + '" data-indice="' + indice + '" class="carrinho-preco" style="width:100px"></td>' +
                '<td data-rotulo="Subtotal" class="mono">' + formatarMoeda(subtotal) + '</td>' +
                '<td><button type="button" class="btn btn-sm btn-outline carrinho-remover" data-indice="' + indice + '">Remover</button></td>';
            corpo.appendChild(tr);
        });

        totalEl.textContent = formatarMoeda(total);
        itensInput.value = JSON.stringify(carrinho.map(function (item) {
            return {
                produto_id: item.id,
                quantidade: item.quantidade,
                preco_unit_venda: item.preco_unit_venda,
            };
        }));
    }

    function adicionarProduto(produto) {
        var existente = carrinho.find(function (item) { return item.id === produto.id; });
        if (existente) {
            if (existente.quantidade < produto.estoque) existente.quantidade += 1;
        } else {
            carrinho.push({
                id: produto.id,
                rotulo: produto.rotulo,
                estoque: produto.estoque,
                preco_unit_venda: parseFloat(produto.preco),
                quantidade: 1,
            });
        }
        atualizar();
    }

    function buscarProdutos(termo) {
        termo = termo.trim().toLowerCase();
        if (!termo) return [];
        var palavras = termo.split(/\s+/);
        return produtos.filter(function (p) {
            var alvo = p.rotulo.toLowerCase();
            return palavras.every(function (palavra) { return alvo.indexOf(palavra) !== -1; });
        }).slice(0, 15);
    }

    function renderizarSugestoes(lista) {
        if (!lista.length) {
            sugestoesBox.innerHTML = '';
            sugestoesBox.classList.remove('aberto');
            return;
        }
        sugestoesBox.innerHTML = lista.map(function (p) {
            return '<div class="sugestao-item" data-id="' + p.id + '">' +
                '<span>' + p.rotulo + '</span>' +
                '<span class="texto-fraco">' + formatarMoeda(parseFloat(p.preco)) + ' · estoque ' + p.estoque + '</span>' +
                '</div>';
        }).join('');
        sugestoesBox.classList.add('aberto');
    }

    busca.addEventListener('input', function () {
        renderizarSugestoes(buscarProdutos(busca.value));
    });

    sugestoesBox.addEventListener('click', function (evento) {
        var item = evento.target.closest('.sugestao-item');
        if (!item) return;
        var produto = produtos.find(function (p) { return String(p.id) === item.dataset.id; });
        if (produto) adicionarProduto(produto);
        busca.value = '';
        sugestoesBox.innerHTML = '';
        sugestoesBox.classList.remove('aberto');
        busca.focus();
    });

    corpo.addEventListener('input', function (evento) {
        var indice = evento.target.dataset.indice;
        if (indice === undefined) return;
        indice = parseInt(indice, 10);
        if (evento.target.classList.contains('carrinho-qtd')) {
            var max = carrinho[indice].estoque;
            var valor = Math.max(1, Math.min(parseInt(evento.target.value || '1', 10), max));
            carrinho[indice].quantidade = valor;
        } else if (evento.target.classList.contains('carrinho-preco')) {
            carrinho[indice].preco_unit_venda = parseFloat(evento.target.value || '0');
        }
        atualizar();
    });

    corpo.addEventListener('click', function (evento) {
        if (!evento.target.classList.contains('carrinho-remover')) return;
        var indice = parseInt(evento.target.dataset.indice, 10);
        carrinho.splice(indice, 1);
        atualizar();
    });

    document.addEventListener('click', function (evento) {
        if (!sugestoesBox.contains(evento.target) && evento.target !== busca) {
            sugestoesBox.classList.remove('aberto');
        }
    });

    if (form) {
        form.addEventListener('submit', function (evento) {
            if (carrinho.length === 0) {
                evento.preventDefault();
                alert('Adicione ao menos um produto.');
            }
        });
    }

    atualizar();
})();
