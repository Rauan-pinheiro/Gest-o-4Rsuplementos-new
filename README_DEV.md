# README_DEV — Guia rápido (4R Suplementos)

Sistema de gestão para loja de suplementos, feito em **Django 6** + **PostgreSQL**, com deploy via **Docker Compose** (Django + Postgres + Caddy). É um sistema **privado**: todas as páginas exigem login (`suplementos/middleware.py`), não existe cadastro público de usuários — o único usuário é o superusuário criado a partir do `.env`.

---

## 1. Como acessar o sistema

- **URL do sistema (frontend)**: a raiz do domínio, ex. `https://seu-dominio.com.br/` → redireciona para `/login/` se você não estiver autenticado.
- **Login**: usuário e senha são os do superusuário (ver seção 3). Não há tela de "criar conta".
- Depois de logado, você cai no **dashboard** (`views.dashboard_view`, rota `''`), e o menu dá acesso a: Produtos, Vendas, Histórico, Inadimplentes, Orçamento, Promoções, Validades, Clientes.

## 2. Como acessar o admin

- **URL do admin**: `https://seu-dominio.com.br/admin/` (Django Admin padrão, `config/urls.py:8`).
- **Login do admin**: as mesmas credenciais do superusuário (é o mesmo usuário — não existe um admin separado).
- No admin dá pra gerenciar diretamente: Locais, Categorias, Produtos, Clientes, Vendas (com itens inline), Orçamentos, Promoções (ver `suplementos/admin.py`).
- Use o admin principalmente para correções pontuais de dados; o uso do dia a dia é pelo frontend.

### Credenciais do superusuário

O superusuário **não é criado manualmente** — ele é criado (ou atualizado) automaticamente toda vez que o container sobe, a partir de 3 variáveis no `.env`:

```
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=voce@exemplo.com
DJANGO_SUPERUSER_PASSWORD=troque-por-uma-senha-forte
```

Isso acontece em [entrypoint.sh](entrypoint.sh) (`python manage.py createsuperuser --noinput`, que lê `DJANGO_SUPERUSER_PASSWORD` do ambiente automaticamente).

⚠️ O `.env` atual (dev local) tem uma senha gerada só para desenvolvimento — **troque `DJANGO_SUPERUSER_PASSWORD`, `POSTGRES_PASSWORD` e `DJANGO_SECRET_KEY` antes de ir para produção** (ver checklist na seção 5).

---

## 3. Rodando localmente

Você tem duas opções: **Docker (recomendado, igual produção)** ou **venv Python puro**.

### Opção A — Docker (recomendado)

Pré-requisito: Docker Desktop instalado e rodando.

```powershell
# 1. copie o .env de exemplo (se ainda não tiver um .env)
Copy-Item .env.example .env
# edite o .env com valores locais (pode manter DJANGO_DEBUG=True)

# 2. suba os containers
docker compose up --build

# 3. acesse
# http://localhost/         -> sistema (o Caddy escuta na porta 80)
# http://localhost/admin/   -> django admin
```

O `entrypoint.sh` já roda `migrate`, `collectstatic` e cria o superusuário automaticamente a cada subida.

Para importar os dados legados dos backups (`backups/*.json`) num banco novo:

```powershell
docker compose exec web python manage.py importar_backups
```

### Opção B — venv local (sem Docker)

Já existe uma venv em `./venv` (Python 3.13). Você vai precisar de um Postgres rodando localmente (ou apontar `POSTGRES_HOST`/porta para um Postgres existente).

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# garanta que .env aponta para um Postgres acessível
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.

---

## 4. Onde estão as coisas (mapa rápido)

| O quê | Onde |
|---|---|
| Configurações Django | [config/settings.py](config/settings.py) |
| Rotas globais (`/admin`, `/login`, `/logout`) | [config/urls.py](config/urls.py) |
| Rotas do sistema (produtos, vendas, etc.) | [suplementos/urls.py](suplementos/urls.py) |
| Views | [suplementos/views/](suplementos/views/) |
| Modelos (Produto, Venda, Cliente, ...) | [suplementos/models.py](suplementos/models.py) |
| Django Admin customizado | [suplementos/admin.py](suplementos/admin.py) |
| Middleware de login obrigatório | [suplementos/middleware.py](suplementos/middleware.py) |
| Importador de backups legados | [suplementos/management/commands/importar_backups.py](suplementos/management/commands/importar_backups.py) |
| Variáveis de ambiente (exemplo) | [.env.example](.env.example) |
| Container da aplicação | [Dockerfile](Dockerfile) |
| Orquestração (Django + Postgres + Caddy) | [docker-compose.yml](docker-compose.yml) |
| Proxy reverso + HTTPS automático | [Caddyfile](Caddyfile) |
| Script de boot do container | [entrypoint.sh](entrypoint.sh) |

---

## 5. Plataforma recomendada para deploy

O projeto **já vem pronto para um VPS com Docker**: `docker-compose.yml` sobe três serviços (Postgres, Django/gunicorn, e Caddy fazendo proxy reverso + HTTPS automático via Let's Encrypt usando `SITE_DOMAIN`). Essa arquitetura é feita sob medida para um VPS simples, então é o caminho de menor esforço — nada precisa ser reescrito.

**Recomendação: VPS com Docker — DigitalOcean Droplet ou Hetzner Cloud.**

- **Hetzner Cloud**: melhor custo-benefício (planos a partir de ~€4/mês), servidores na Europa/EUA. Ótimo se não precisar de baixa latência específica pro Brasil.
- **DigitalOcean**: um pouco mais caro, mas tem datacenter em São Paulo (menor latência para usuários no Brasil) e documentação/suporte mais simples para quem está começando com VPS.

Por que VPS em vez de uma PaaS (Render, Railway, Fly.io)?
- Para um sistema pequeno de uso interno como este, um VPS de ~$4–6/mês com Docker Compose é mais barato e mais previsível do que os planos pagos dessas PaaS.

Dito isso, o projeto **também está pronto para deploy na Railway** (ver seção 6) — é a opção mais simples se você preferir não gerenciar servidor.

### Passo a passo do deploy num VPS (Ubuntu, Docker)

1. **Provisionar o servidor**: crie o Droplet/servidor (Ubuntu 22.04+), aponte o DNS do seu domínio (`SITE_DOMAIN`) para o IP do servidor (registro A).
2. **Instalar Docker**: `curl -fsSL https://get.docker.com | sh` (inclui Docker Compose plugin).
3. **Enviar o código** para o servidor (`git clone` do repositório, ou `scp`/`rsync`).
4. **Criar o `.env` de produção** a partir de `.env.example`, preenchendo:
   - `DJANGO_SECRET_KEY`: gere uma nova (nunca reaproveite a de dev). Ex.: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
   - `DJANGO_DEBUG=False`
   - `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS`: seu domínio real
   - `POSTGRES_PASSWORD`: senha forte nova
   - `DJANGO_SUPERUSER_*`: usuário/senha reais de acesso
   - `SITE_DOMAIN`: seu domínio (o Caddy usa isso para emitir HTTPS automaticamente)
5. **Abrir as portas 80 e 443** no firewall do servidor (necessário para o Caddy emitir/renovar o certificado Let's Encrypt).
6. **Subir os containers**: `docker compose up -d --build`
7. **Conferir logs**: `docker compose logs -f web` — confirme que migrations rodaram e o superusuário foi criado sem erro.
8. **Testar**: acesse `https://seu-dominio.com.br/` (login) e `https://seu-dominio.com.br/admin/`.
9. **(Opcional) Importar dados legados**: `docker compose exec web python manage.py importar_backups`
10. **Backups**: configure um backup periódico do volume `postgres_data` (ex. `pg_dump` agendado via cron) — hoje não existe rotina automática de backup no projeto.

### Checklist antes de ir pra produção

- [ ] `.env` de produção com `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` e `DJANGO_SUPERUSER_PASSWORD` **diferentes** dos valores de dev
- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS` com o domínio real (não `localhost`)
- [ ] DNS do domínio apontando para o IP do servidor antes de subir o Caddy (senão a emissão do certificado HTTPS falha)
- [ ] Portas 80/443 liberadas no firewall
- [ ] `.env` **não** commitado no git (já está no `.gitignore`, mas confira)
- [ ] Rotina de backup do Postgres definida

---

## 6. Deploy na Railway

O projeto está preparado para deploy direto na [Railway](https://railway.com/) sem precisar do `docker-compose.yml`/Caddy — a Railway já cuida de HTTPS, domínio e porta dinâmica sozinha. O `Dockerfile` existente é usado como está (a Railway detecta e builda ele automaticamente); `railway.json` define o healthcheck (`/healthz/`).

### Passo a passo

1. **Criar o projeto na Railway** a partir do repositório Git (GitHub).
2. **Adicionar um banco PostgreSQL** ao projeto (botão "New" → "Database" → "PostgreSQL"). A Railway cria a variável `DATABASE_URL` automaticamente — o `config/settings.py` já detecta e usa essa variável quando presente (ver seção de banco de dados).
3. **Conectar o Postgres ao serviço web**: na aba "Variables" do serviço web, referencie `DATABASE_URL` do Postgres (a Railway sugere isso automaticamente ao ligar os dois serviços).
4. **Definir as variáveis de ambiente do serviço web** (aba "Variables"):
   - `DJANGO_SECRET_KEY` — gere uma nova, nunca reaproveite a de dev.
   - `DJANGO_DEBUG=False`
   - `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS` — normalmente nem precisa definir: o projeto detecta `RAILWAY_PUBLIC_DOMAIN` (injetada automaticamente pela Railway) e libera esse domínio sozinho. Só defina essas duas se for usar um domínio próprio além do `*.up.railway.app`.
   - `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` — credenciais do único usuário do sistema.
   - Não defina `PORT` — a Railway injeta essa variável sozinha, e o `entrypoint.sh` já usa `$PORT` automaticamente.
5. **Gerar o domínio público** do serviço web (aba "Settings" → "Networking" → "Generate Domain").
6. **Deploy**: a Railway builda a imagem, e o `entrypoint.sh` roda `migrate`, `collectstatic` e cria o superusuário automaticamente a cada deploy — igual ao fluxo do VPS.
7. **Testar**: acesse a URL gerada (`/` → login) e `/admin/`.
8. **(Opcional) Importar dados legados**: rode `python manage.py importar_backups` pelo shell da Railway (aba do serviço → "..." → "Run command", ou via CLI `railway run python manage.py importar_backups`).

O projeto não usa upload de arquivos (não há campo de imagem em nenhum model), então não depende de disco persistente — funciona no filesystem efêmero padrão de qualquer serviço Railway, sem Volume nem storage externo.

### Checklist antes do deploy na Railway

- [ ] Serviço PostgreSQL adicionado e `DATABASE_URL` conectada ao serviço web
- [ ] `DJANGO_SECRET_KEY`, `DJANGO_SUPERUSER_PASSWORD` de produção definidos (diferentes dos de dev)
- [ ] `DJANGO_DEBUG=False`
- [ ] Domínio público gerado na aba Networking
- [ ] `.env` não commitado no git (confirmado no `.gitignore`)

---

## 7. Deploy gratuito (opção alternativa — Render + Neon)

Também é possível colocar o sistema no ar sem custo, mas exige adaptar a arquitetura atual: o `docker-compose.yml` (Postgres + Caddy) foi pensado para VPS, e tiers gratuitos de PaaS normalmente não dão banco Postgres persistente nem disco persistente de graça.

**Combinação sugerida:**
- **App Django**: [Render](https://render.com) free tier (roda o `gunicorn`; "dorme" após ~15 min sem uso, com cold start de 30–50s no primeiro acesso; filesystem efêmero).
- **Banco de dados**: [Neon](https://neon.tech) free tier (Postgres serverless persistente).

Como o projeto não depende de disco persistente (sem upload de arquivos), o filesystem efêmero do Render free não é um problema aqui.

Essa opção é razoável para um sistema interno pequeno como este — o principal incômodo do dia a dia é o cold start do plano free.

### Checklist se essa opção for escolhida

- [ ] Criar conta e projeto no Render (web service apontando pro repositório)
- [ ] Criar banco no Neon e copiar as credenciais (host, porta, usuário, senha, nome do banco)
- [ ] Remover o serviço `db` do `docker-compose.yml` (ou não usar compose no Render) e apontar `POSTGRES_HOST`/`POSTGRES_PORT`/`POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` no `.env` para o Neon
- [ ] Remover/ajustar o Caddy (Render já cuida de HTTPS e domínio automaticamente) — o `Caddyfile` deixa de ser necessário nesse cenário
- [ ] Atualizar `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS` para o domínio `.onrender.com` (ou domínio próprio, se configurado no Render)
- [ ] Definir `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` e `DJANGO_SUPERUSER_PASSWORD` de produção (diferentes dos de dev)
- [ ] Definir `DJANGO_DEBUG=False`
- [ ] Rodar `migrate` e criar o superusuário no primeiro deploy (via shell do Render ou build command)
- [ ] Avaliar o limite de inatividade do Neon free (pode pausar o banco após período sem uso) e o cold start do Render free antes de considerar essa opção para uso com usuários externos
