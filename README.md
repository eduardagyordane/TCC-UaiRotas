# UaiRotas

Sistema web desenvolvido como parte do TCC **Otimização da Gestão de Equipes Externas por Meio de Monitoramento Geolocalizado e Análise Temporal de Rotas**.

## Tecnologias

- Python 3.12+
- Flask
- HTML com Jinja2
- CSS e JavaScript
- SQLite
- Pytest

## Executar localmente

```bash
python -m venv .venv
```

No Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
flask --app run.py init-db
flask --app run.py create-admin
flask --app run.py run --debug
```

Acesse `http://127.0.0.1:5000/login`.

Antes de usar o sistema fora do ambiente local, altere `SECRET_KEY` no arquivo `.env`.

## Testes

```bash
pytest -q
```

Para gerar o relatório de cobertura:

```bash
pytest --cov=uairotas --cov-report=term-missing
```

