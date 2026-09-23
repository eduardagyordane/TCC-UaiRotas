# UaiRotas

Sistema web desenvolvido para o TCC **Otimização da Gestão de Equipes Externas por Meio de Monitoramento Geolocalizado e Análise Temporal de Rotas**.

Nesta etapa estão implementadas a autenticação administrativa, a Home operacional e os módulos de Rotas, Frotas, Relatórios e Usuários. Os dados operacionais exibidos são demonstrativos e estão preparados para serem substituídos pelas integrações com Cobli e IXC.

## Funcionalidades disponíveis

- Login protegido com sessão, senha armazenada por hash e proteção CSRF.
- Home acessível somente após autenticação.
- Menu superior com Home, Rotas, Frota, Relatórios e Usuários.
- Perfil do usuário com encerramento seguro da sessão.
- Temas claro e escuro com preferência salva no navegador.
- Indicadores de veículos, técnicos, ordens de serviço e alertas.
- Mapbox GL JS e Directions API, com trajetos ajustados à malha viária, veículos, ordens e locais de interesse.
- Alertas operacionais, incluindo almoço superior a duas horas.
- Alertas sonoros com preferência persistente, controle no cabeçalho e proteção contra repetição na mesma sessão.
- Som aplicado a ocorrências operacionais, manutenção, troca de óleo, desvios e erros de formulário.
- Relação das ordens de serviço do dia.
- Gráfico de desempenho das ordens.
- Layout responsivo para computador, tablet e celular.
- Módulo de Rotas protegido por autenticação.
- Mapa interativo com zoom, movimentação e tela cheia pelos controles do Mapbox.
- Rotas individuais por colaborador, com destaque selecionável.
- Filtros por data, colaborador e situação da ordem de serviço.
- Ordens com cliente, endereço e tipo de serviço.
- Locais de interesse destacados por ícones.
- Módulo de Frotas protegido por autenticação, com resumo de veículos, técnicos, quilometragem, gasolina e locais de interesse.
- Relação de veículos com motorista, odômetro, última e próxima troca de óleo.
- Visão de custos por combustível, manutenção, multas e outros gastos.
- Agenda das próximas manutenções.
- Formulários para veículo, motorista, troca de óleo, abastecimento, multa, outro gasto e manutenção.
- Visão geral dos relatórios com indicadores consolidados de operação, rotas e frota.
- Relatório detalhado de Rotas com produtividade, deslocamentos, ordens, tempos e desvios por colaborador.
- Relatório detalhado de Frotas com quilometragem, consumo, custos, multas e manutenções por veículo.
- Gráficos de linha, barras horizontais e verticais e gráficos de rosca.
- Filtro de período compartilhado entre os relatórios.
- Módulo de Usuários acessível somente por administradores.
- Cadastro persistente de nome, telefone, e-mail, endereço, CPF, data de nascimento e função.
- Perfis de administrador e supervisor, com situação ativa ou inativa.
- Busca por nome, e-mail ou CPF.
- Edição completa dos dados e troca opcional de senha.
- Validação de campos obrigatórios, duplicidade de e-mail e CPF e tamanho mínimo da senha.

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
│   ├── test_fleet.py
│   ├── test_reports.py
│   ├── test_users.py
│   └── test_models.py
└── uairotas/
    ├── __init__.py
    ├── auth.py
    ├── main.py
    ├── models.py
    ├── static/
    │   ├── audio/alarme_sistema.mp3
    │   ├── css/app.css
    │   └── js/
    │       ├── app.js
    │       └── maps.js
    └── templates/
        ├── auth/login.html
        ├── _app_header.html
        ├── base.html
        ├── home.html
        ├── routes.html
        ├── fleet.html
        ├── reports_overview.html
        ├── reports_routes.html
        ├── reports_fleet.html
        └── users.html
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

Em uma instalação criada antes do módulo de Usuários, execute novamente `flask --app run.py init-db`. O comando preserva os registros existentes e adiciona os novos campos de perfil.

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

### Mapbox

Crie uma conta no Mapbox, gere um **token público** com as permissões mínimas necessárias e configure o arquivo `.env`:

```dotenv
MAPBOX_ACCESS_TOKEN=pk.seu_token_publico_aqui
```

O token público precisa chegar ao navegador para carregar o mapa. Proteja-o no painel do Mapbox com restrições de URL. Para desenvolvimento local, autorize `http://127.0.0.1:5000/*` e `http://localhost:5000/*`; em produção, substitua esses endereços pelo domínio real.

O Mapbox possui faixa gratuita mensal, mas exige cadastro e token e pode gerar cobrança se o limite vigente for ultrapassado. Se a variável não estiver configurada, a Home e a tela de Rotas exibem uma orientação no lugar do mapa, sem interromper o restante do sistema.

Os pontos das rotas são enviados à Directions API para que as linhas acompanhem as ruas. Se a consulta falhar, o mapa mantém o traçado GeoJSON original como fallback. A Uploads API não é usada nesse fluxo: ela serve para transformar arquivos geográficos grandes e estáticos em tilesets e exige um token secreto com `uploads:write`, que nunca deve chegar ao navegador ou ao GitHub.

## Testes

Com o ambiente virtual ativado, execute:

```bash
pytest -q
```

Para executar com cobertura:

```bash
pytest -q --cov=uairotas --cov-report=term-missing
```

Os navegadores podem bloquear áudio automático antes da primeira interação do usuário. Quando isso ocorrer, o sino no cabeçalho ficará destacado; basta clicar nele ou interagir com a página para liberar o som. A preferência ativada ou silenciada fica salva no navegador.

Alertas recebidos futuramente pela Cobli ou pelo backend podem usar o mesmo mecanismo:

```javascript
window.dispatchEvent(new CustomEvent("uairotas:alert", {
  detail: { id: `cobli-${evento.id}` },
}));
```

O identificador deve ser único para impedir que a mesma ocorrência reproduza o som mais de uma vez na sessão.

Consulte o resultado validado da versão atual em [`TEST_RESULTS.md`](TEST_RESULTS.md).

## Próximas integrações

Os objetos demonstrativos definidos em `uairotas/main.py` serão substituídos gradualmente por consultas ao banco local, alimentado pelas APIs da Cobli e do IXC. As credenciais dessas APIs deverão permanecer somente no backend, por meio de variáveis de ambiente.

Nesta primeira entrega, os formulários de Frotas validam os campos no servidor e apresentam a confirmação da operação, mas ainda não persistem os registros. A criação das tabelas e modelos de frota será realizada após a aprovação da interface e dos fluxos.
