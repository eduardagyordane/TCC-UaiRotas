# UaiRotas

Sistema web desenvolvido para o TCC **Otimização da Gestão de Equipes Externas por Meio de Monitoramento Geolocalizado e Análise Temporal de Rotas**.

Nesta etapa estão implementadas a autenticação administrativa, a Home operacional e o módulo de Rotas. Os dados exibidos são demonstrativos e estão preparados para serem substituídos pelas integrações com Cobli e IXC.

## Funcionalidades disponíveis

- Login protegido com sessão, senha armazenada por hash e proteção CSRF.
- Home acessível somente após autenticação.
- Menu superior com Home, Rotas, Frota, Relatórios e Usuários.
- Perfil do usuário com encerramento seguro da sessão.
- Temas claro e escuro com preferência salva no navegador.
- Indicadores de veículos, técnicos, ordens de serviço e alertas.
- Mapa operacional demonstrativo com veículos, rota e locais de interesse.
- Alertas operacionais, incluindo almoço superior a duas horas.
- Relação das ordens de serviço do dia.
- Gráfico de desempenho das ordens.
- Layout responsivo para computador, tablet e celular.
- Módulo de Rotas protegido por autenticação.
- Mapa interativo com zoom, movimentação, centralização e tela cheia.
- Rotas individuais por colaborador, com destaque selecionável.
- Filtros por data, colaborador e situação da ordem de serviço.
- Ordens com cliente, endereço e tipo de serviço.
- Locais de interesse destacados por ícones.

## Tecnologias

- Python 3.12+
- Flask 3
- Flask-Login
- Flask-SQLAlchemy
- Flask-WTF
- SQLite
- HTML e Jinja2
- CSS responsivo
- JavaScript sem frameworks
- Pytest e pytest-cov

## Estrutura principal

```text
TCC-UaiRotas/
├── run.py
├── requirements.txt
├── requirements-dev.txt
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_home.py
│   ├── test_routes.py
│   └── test_models.py
└── uairotas/
    ├── __init__.py
    ├── auth.py
    ├── main.py
    ├── models.py
    ├── static/
    │   ├── css/app.css
    │   └── js/app.js
    └── templates/
        ├── auth/login.html
        ├── _app_header.html
        ├── base.html
        ├── home.html
        └── routes.html
```

## Como executar no Windows

Abra o PowerShell na pasta do projeto e execute:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
flask --app run.py init-db
flask --app run.py create-admin
flask --app run.py run --debug
```

O comando `create-admin` solicitará nome, e-mail e senha. A senha não será exibida durante a digitação.

Depois, acesse:

```text
http://127.0.0.1:5000/login
```

Se o PowerShell bloquear a ativação do ambiente virtual, execute apenas na sessão atual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Como executar no Linux ou macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
flask --app run.py init-db
flask --app run.py create-admin
flask --app run.py run --debug
```

## Configuração

O arquivo `.env.example` contém as configurações iniciais. Copie-o para `.env` e troque a `SECRET_KEY` antes de utilizar o sistema fora do ambiente local.

Exemplo para gerar uma chave:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Nunca envie o arquivo `.env`, tokens da Cobli, credenciais do IXC ou o banco de produção para o GitHub.

## Testes

Com o ambiente virtual ativado, execute:

```bash
pytest -q
```

Para executar com cobertura:

```bash
pytest -q --cov=uairotas --cov-report=term-missing
```

Resultado da versão atual: **22 testes aprovados e 91% de cobertura total**. Consulte também [`TEST_RESULTS.md`](TEST_RESULTS.md).

## Próximas integrações

Os objetos demonstrativos definidos em `uairotas/main.py` serão substituídos gradualmente por consultas ao banco local, alimentado pelas APIs da Cobli e do IXC. As credenciais dessas APIs deverão permanecer somente no backend, por meio de variáveis de ambiente.
