# Atualizar os relatórios — 25/09/2026

O pacote contém o projeto completo. As telas agora têm conteúdos distintos:

- **Resumo:** principais indicadores de frota e atendimentos.
- **Frota:** combustível, óleo, multas, despesas, manutenção e custo por veículo.
- **Rotas:** OS, produtividade, deslocamentos, atendimento, almoço e desvios.

Todas aceitam período, veículo e motorista. Os filtros também acompanham a troca de aba e a exportação. Preencha `MAPBOX_ACCESS_TOKEN` no seu arquivo local `.env` com o token público Mapbox informado anteriormente; o código no GitHub não inclui o token.

## Se você já executa o projeto

1. Pare o Flask com `Ctrl+C`.
2. Faça uma cópia da pasta atual do projeto, incluindo seu banco e sua configuração. O banco padrão fica em `instance/uairotas.db`; se você alterou `DATABASE_URL`, preserve o arquivo daquele caminho.
3. Extraia o ZIP. Copie o conteúdo da pasta interna `UaiRotas` para a pasta atual do projeto, substituindo o código. Mantenha seu `.env`, sua pasta `instance` e seu ambiente virtual. Inclua a pasta nova `uairotas/templates/reports/`.
4. No terminal, entre na pasta que contém `run.py` e `requirements.txt`. Execute:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app run.py init-db
.\.venv\Scripts\python.exe -m flask --app run.py run
~~~

Se o ambiente virtual já estiver ativado e estiver em outra pasta, substitua `.\.venv\Scripts\python.exe` por `python`. Não é necessário ativar scripts do PowerShell ao utilizar o caminho completo do executável.

O comando `init-db` adiciona o vínculo de veículo nas OS e preserva os registros existentes. Ele deve ser executado antes de abrir o site atualizado. Não crie outro administrador e não execute `seed-demo` no banco atual.

Abra <http://127.0.0.1:5000/relatorios>, entre com sua conta e aplique os filtros. Despesas antigas sem motorista e OS sem veículo permanecem na opção “Todos”; não recebem vínculos reais inventados. O motorista de uma despesa pode ser informado ao editar o lançamento na Frota.

## Instalação nova e testes

Siga o [README.md](README.md) para criar o ambiente, configurar a chave de sessão e cadastrar seu administrador. A pasta correta é a **UaiRotas dentro do ZIP**, não a pasta externa que contém o ZIP.

Para executar os testes Python:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
~~~

Os resultados e os testes opcionais de JavaScript estão em [TEST_RESULTS.md](TEST_RESULTS.md).
