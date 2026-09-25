# UaiRotas

Sistema web do TCC para gestão e análise de equipes externas. Esta revisão aplicou as correções de funcionalidade, segurança, visual e desempenho descritas no relatório de 24/09/2026.

**Tecnologias mantidas:** Python 3.12, Flask, Jinja2, HTML, CSS, JavaScript e SQLite. Mapbox GL JS 3.30.0 foi mantido para o mapa. Node.js foi utilizado apenas nos testes de JavaScript; não é necessário para executar o site.

## Situação desta versão

- Login, Home, Rotas, Frota, Relatórios, Usuários, Meu perfil e Central de alertas.
- Cadastros e edições da Frota persistidos no SQLite, com validação e histórico de alterações.
- Indicadores e gráficos calculados dos registros e do período selecionado.
- Relatórios separados em Resumo, Frota e Rotas, com filtros combinados por período, veículo e motorista.
- Mapbox com rotas por colaborador, filtros, ícones, popups, troca de tema, recuperação de falhas e indicação de rota aproximada.
- Som aprovado preservado, volume, categorias e reconhecimento de alertas.
- **Cobli e IXC ainda não conectados.** A base inicia sem dados operacionais. Os exemplos só são inseridos pelo comando opcional `seed-demo`.
- Código e instruções para execução local. A publicação no GitHub não implanta o sistema em produção.

## Executar no Windows

Requisitos: Python 3.12 e acesso à internet para instalar dependências. Extraia o ZIP e abra no terminal a pasta interna **UaiRotas**, que contém `run.py`, `requirements.txt` e `requirements-dev.txt`. Se o terminal estiver na pasta externa do pacote, execute `cd .\UaiRotas` primeiro. No PowerShell:

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
~~~

Copie a chave gerada para `SECRET_KEY` no arquivo `.env`. Nesse mesmo arquivo, preencha `MAPBOX_ACCESS_TOKEN` com seu token público do Mapbox.

~~~powershell
.\.venv\Scripts\python.exe -m flask --app run.py init-db
.\.venv\Scripts\python.exe -m flask --app run.py create-admin
.\.venv\Scripts\python.exe -m flask --app run.py run
~~~

Informe nome, e-mail e senha quando solicitado. **Não existe senha padrão.** Abra <http://127.0.0.1:5000> e entre com a conta criada. Não é necessário ativar o ambiente virtual nem alterar a política de execução do PowerShell.

## Executar no Linux ou macOS

~~~bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -c "import secrets; print(secrets.token_hex(32))"
~~~

Preencha a chave gerada em `SECRET_KEY` e seu token público do Mapbox em `MAPBOX_ACCESS_TOKEN`, no arquivo `.env`. Depois:

~~~bash
.venv/bin/python -m flask --app run.py init-db
.venv/bin/python -m flask --app run.py create-admin
.venv/bin/python -m flask --app run.py run
~~~

O comando `flask run` atende ao desenvolvimento local. Encerre com Ctrl+C.

## Dados demonstrativos opcionais

Depois de criar o administrador, em uma base operacional vazia:

~~~powershell
.\.venv\Scripts\python.exe -m flask --app run.py seed-demo
~~~

No Linux/macOS, substitua o executável por `.venv/bin/python`.

São criados três colaboradores e veículos, 35 dias de viagens e OS, gastos, manutenção e locais fictícios. As telas exibem “Dados demonstrativos”. Os documentos pessoais de demonstração são deliberadamente inválidos; para editar um motorista demonstrativo, substitua-os por dados de teste que satisfaçam as validações. Validação sintática de CPF/CNH não comprova identidade.

O comando não cria usuários, não consulta APIs, recusa uma base operacional já preenchida e fica bloqueado em produção. Não misture demonstração com operação real: utilize bancos separados.

## Atualizar uma instalação existente

1. Encerre o servidor e preserve sua configuração `.env`.
2. Copie o arquivo de banco existente para um local de backup. Na configuração padrão ele fica em `instance/uairotas.db`. Confira `DATABASE_URL` se utilizou outro caminho.
3. Copie o conteúdo da pasta `UaiRotas` do ZIP para a pasta atual do projeto, substituindo o código e mantendo seu banco, `.env` e ambiente virtual. Copie também a subpasta nova `uairotas/templates/reports/`.
4. Atualize as dependências e execute `flask --app run.py init-db` usando o Python do ambiente virtual.
5. Inicie o site e entre novamente. A nova versão da autenticação invalida sessões antigas.

A migração 1 adiciona colunas ausentes de Usuários, cria as tabelas operacionais e protege o último administrador ativo. A migração 2 adiciona o vínculo histórico entre uma OS e seu veículo para permitir o filtro por carro. Executar `init-db` novamente não recria nem apaga os cadastros. Somente os exemplos demonstrativos com associação inequívoca recebem vínculos retroativos; registros reais sem vínculo permanecem sem atribuição.

Depois de copiar os arquivos, execute na pasta que contém `run.py`:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app run.py init-db
.\.venv\Scripts\python.exe -m flask --app run.py run
~~~

Se seu ambiente virtual já estiver ativado, use `python` no lugar de `.\.venv\Scripts\python.exe`. **Execute `init-db` antes de abrir as novas telas**: ele adiciona a coluna necessária aos filtros. As contas existentes continuam válidas; não é necessário criar outro administrador.

Uma versão antiga que não persistia formulários de Frota não possui registros recuperáveis a partir das mensagens de sucesso daquela versão.

Nunca execute `seed-demo` no banco da operação para “atualizar” dados.

## Backup e restauração

Com esta versão instalada, use um caminho novo:

~~~powershell
.\.venv\Scripts\python.exe -m flask --app run.py backup-db --output backups/uairotas-2026-09-25.db
~~~

O comando utiliza o mecanismo de backup do SQLite, gera um snapshot consistente e recusa sobrescrever arquivos. Escolha um nome diferente para cada backup. O arquivo contém dados pessoais e hashes de senha; mantenha-o com acesso restrito e fora do Git.

Para restaurar:

1. Pare o servidor.
2. Preserve uma cópia do banco atual.
3. Copie o backup para o caminho configurado em `DATABASE_URL`.
4. Execute `init-db`, reinicie e confira o acesso e os cadastros.

Os testes verificam a integridade e o conteúdo restaurável do snapshot com uma base sintética. A política de retenção e as cópias externas da empresa dependem da implantação.

## Uso e permissões

| Ação | Admin | Supervisor |
| --- | --- | --- |
| Home, Rotas, Frota e Relatórios | Consultar | Consultar |
| Exportar CSV e imprimir relatórios | Sim | Sim |
| Cadastrar/editar Frota e concluir manutenção | Sim | Não |
| Dados cadastrais completos de motoristas e fotos | Sim | Não |
| Gerenciar Usuários e consultar dados completos | Sim | Não |
| Editar o próprio perfil | Sim | Sim |
| Reconhecer alertas para a própria conta | Sim | Sim |

- **Frota:** “Adicionar à frota” reúne veículo, motorista, óleo, abastecimento, multa, outro gasto e manutenção. Cadastros salvos aparecem nas listas e nos totais.
- **Óleo:** última/próxima troca, odômetro, próxima quilometragem e valor. Leituras não podem diminuir o odômetro nem contradizer registros anteriores.
- **Edição de leitura histórica:** veículo, data e quilometragem permanecem preservados. Para atualizar o odômetro, registre uma nova leitura; os demais campos podem ser corrigidos.
- **Manutenção:** agendamentos têm valor estimado. “Concluir” solicita data da realização e valor pago e passa a contabilizá-los nos custos. Nesta versão, a data do lançamento concluído passa a ser a data de realização; o log registra o evento, sem guardar uma cópia completa dos valores anteriores.
- **Fotos:** PNG/JPEG de até 512 KB e 16 megapixels, decodificadas, reduzidas a até 256 × 256 e gravadas como JPEG sem metadados EXIF.
- **Usuários:** busca por nome/e-mail/CPF, páginas de 25 itens e um único diálogo de edição. CPF mascarado na listagem; endereço e nascimento ficam no detalhe autorizado.
- **Perfil:** alterações de e-mail/senha exigem a senha atual. Mudanças de senha, e-mail, função ou situação invalidam outras sessões e cookies de “Lembrar de mim”.
- **Administração:** não é permitido desativar o próprio usuário nem remover/rebaixar o último admin ativo. A regra do último admin também é protegida no banco.

## Cálculos e relatórios

| Tela | Conteúdo |
| --- | --- |
| **Resumo** | Custos, quilometragem, OS concluídas e taxa de conclusão; gráficos de composição dos gastos e situação dos atendimentos; atalhos para os detalhes |
| **Frota** | Combustível, óleo, multas, outros gastos, manutenção, custo/km e distância dos veículos; gráficos de custos e preço da gasolina; lançamentos paginados |
| **Rotas** | OS, produtividade por motorista, deslocamento, atendimento, almoço acima de duas horas e desvios; gráficos de ordens, situação e distribuição do tempo |

Os três filtros — **período, veículo e motorista** — funcionam em conjunto. Clique em “Aplicar filtros” para atualizar cartões, gráficos e tabelas. A seleção é mantida ao trocar de aba, navegar entre páginas dos lançamentos ou exportar CSV. “Limpar” restaura todos os veículos e motoristas e o período padrão de 30 dias. A impressão identifica os filtros aplicados.

O motorista considerado é o vinculado ao lançamento/viagem/OS na época do registro. Trocar o motorista atual do veículo não muda relatórios antigos. Nos formulários de despesas da Frota, o campo “Motorista do lançamento” permite informar esse vínculo; ele é obrigatório para multas e opcional nos demais tipos. Gastos sem motorista aparecem somente quando esse filtro está em “Todos os motoristas”. Para atribuir um gasto antigo, edite seu cadastro na Frota.

O filtro de veículo nas OS usa o veículo registrado no atendimento. OS antigas sem esse vínculo permanecem em “Todos os veículos”; o sistema não deduz qual carro foi utilizado a partir do vínculo atual do motorista. O cadastro desse vínculo nas integrações futuras deverá usar o identificador histórico correto.

Valores monetários são armazenados em **centavos inteiros**, volumes em **mililitros** e distâncias em **metros**. Abastecimentos calculam litros × preço por litro, arredondando o total para centavos com a regra decimal `ROUND_HALF_UP`.

- Períodos inclusivos de 7, 30 ou 90 dias e ano corrente, considerando `America/Sao_Paulo`.
- Custos realizados excluem manutenções ainda agendadas e lançamentos fora do intervalo.
- Custos sem veículo vinculado entram no total e aparecem separadamente no detalhamento quando o filtro de veículo está em “Todos os veículos”.
- Custo por km usa custos e distâncias do mesmo período; sem distância, não há divisão nem valor inventado.
- Preço do combustível por data é a média ponderada pelos litros, com eixo iniciado em zero.
- OS concluídas, produtividade, distância e tempos provêm das mesmas consultas utilizadas nos cartões e tabelas.
- Os tempos exibidos são os valores registrados em viagens/OS, não uma medição automática da jornada.
- Não é calculado consumo em km/L a partir de abastecimentos sem associação adequada a leituras e ciclos de tanque.
- Rosca de custos, colunas por data, barras de produtividade/custo por km, linha do preço e barras de tempo possuem valores textuais ou tabelas alternativas.
- CSV exporta o resumo tabular específico da aba, com os mesmos filtros e totais: custos/OS por data no Resumo, distância/custos por veículo na Frota e desempenho por motorista em Rotas. A primeira linha identifica período, carro e motorista. Usa separador ponto e vírgula e UTF-8 com BOM. Os valores monetários das colunas de custo são identificados em **centavos**; distâncias são identificadas em **metros**. Textos são protegidos contra interpretação como fórmula por planilhas.
- “Imprimir / PDF” usa a impressão do navegador. Selecione “Salvar como PDF”; as tabelas alternativas são abertas para a impressão. Na Frota, a tabela de lançamentos imprime a página atual de até 25 registros, enquanto os indicadores e gráficos resumem todo o período filtrado.

As ocorrências no relatório de Rotas respeitam o período, carro e motorista selecionados. As pendências atuais continuam na Central de alertas, acessível por um link próprio.

## Mapbox

Configure `MAPBOX_ACCESS_TOKEN` no seu arquivo local `.env`, mantendo o valor completo do token público fornecido para o projeto. O arquivo `.env.example` contém apenas o nome da variável; o token real fica fora do Git. Uma variável definida no ambiente tem prioridade sobre o `.env`.

Se você utilizava a cópia anterior com o token dentro de `config.py`, transfira o valor para `MAPBOX_ACCESS_TOKEN` no `.env` antes de atualizar. Reinicie o Flask após preencher ou alterar o token. Sem esse valor, a aplicação informa a ausência de configuração do mapa e mantém as listas disponíveis.

O token público é enviado ao navegador por necessidade do mapa; restrinja seus domínios e permissões no painel do Mapbox. Tokens secretos de servidor não pertencem ao frontend.

A aplicação utiliza **Mapbox GL JS** e **Directions API**. A API de Uploads envia conjuntos de dados para o provedor e não foi necessária para desenhar as rotas desta versão. Não há processo de upload de dados para o Mapbox no projeto.

- Fontes e camadas reaplicam a geometria já obtida ao trocar entre temas.
- As consultas de Directions têm limite de 10 segundos; em falha, a ligação aproximada fica explicitamente identificada e pode ser recalculada.
- O cache em memória evita chamadas duplicadas na página. Entre navegações, é respeitado o cache HTTP do provedor; não há armazenamento permanente de respostas de Directions.
- Cada consulta aceita até 25 pontos. Divisão de roteiros maiores e otimizações para centenas de marcadores dependem de evolução posterior.
- O foco em um colaborador filtra linhas e marcadores associados; “Mostrar todas” restaura a visualização.
- Pontos de interesse usam ícones de base, depósito, restaurante e posto. OS mostram cliente, endereço, serviço e situação.
- A animação ocorre no elemento interno do marcador, preservando o posicionamento do Mapbox, e respeita a preferência de movimento reduzido.
- Rotas calculadas entre pontos são **planejadas**, não comprovação do caminho percorrido. O projeto não inventa posições em tempo real.
- Sem acesso autorizado ao Mapbox, rede ou WebGL, as listas continuam disponíveis e o mapa mostra uma mensagem.

Uso, limites e cobrança dependem da conta do Mapbox. Nenhuma chamada real foi necessária para executar os testes automatizados.

## Alertas sonoros

O arquivo aprovado `uairotas/static/audio/alarme_sistema.mp3` foi preservado integralmente e é carregado sob demanda.

O menu do perfil contém volume, botão de teste e categorias Rotas/Frota/Formulários. O sino ativa ou silencia; após bloqueio inicial do navegador, o clique tenta liberar a reprodução. Há sempre um aviso visual correspondente.

Eventos operacionais usam o mesmo identificador nas diferentes páginas. Um evento ouvido não é repetido a cada navegação da mesma sessão do navegador. “Marcar como visto” persiste por usuário e não significa resolver a ocorrência. Erros distintos de formulário recebem IDs distintos.

As regras locais abrangem almoço acima de 120 minutos, OS atrasadas, desvios registrados, troca de óleo em até 500 km ou 7 dias e manutenção próxima/atrasada. Não existe ainda recebimento de eventos em tempo real da Cobli/IXC. O evento JavaScript `uairotas:alert` é apenas um ponto de integração futuro.

## Testes

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q --cov=uairotas --cov-report=term-missing
node --test tests/frontend/core.test.cjs tests/frontend/maps.test.cjs
~~~

Use Node.js 24 para os testes JavaScript. No Linux/macOS, substitua o Python pelo caminho `.venv/bin/python`. As bases de testes são sintéticas e isoladas em memória.

O resultado local desta revisão está em [TEST_RESULTS.md](TEST_RESULTS.md). O fluxo de GitHub Actions está em `.github/workflows/tests.yml` e executa os testes em pushes e pull requests. Consulte a aba Actions do repositório para acompanhar os resultados remotos.

## Configuração e produção

| Variável | Uso |
| --- | --- |
| `APP_ENV` | `development` local; `production` na implantação |
| `SECRET_KEY` | Chave aleatória para a sessão e o CSRF |
| `DATABASE_URL` | Padrão SQLite em `instance/uairotas.db` |
| `TIMEZONE` | Padrão `America/Sao_Paulo` |
| `MAPBOX_ACCESS_TOKEN` | Token público do mapa |
| `TRUSTED_HOSTS` | Domínios autorizados, separados por vírgula, sem protocolo |
| `FLASK_DEBUG` | Manter `0` em produção |

Em produção, configure HTTPS, `APP_ENV=production`, `FLASK_DEBUG=0`, hosts autorizados e chave aleatória de pelo menos 32 caracteres. A aplicação recusa a chave padrão/exemplo e a ausência de hosts nessa modalidade e ativa cookies Secure e HSTS.

Use servidor WSGI apropriado para o ambiente, supervisionado por serviço e publicado por proxy HTTPS. O servidor de desenvolvimento do Flask não é a implantação. Configure cabeçalhos de proxy somente para a infraestrutura confiável utilizada; esta versão não aceita automaticamente um `X-Forwarded-For` fornecido pelo cliente.

Há CSRF, hash de senha, cookies HttpOnly/SameSite, CSP, bloqueio de enquadramento, limites de upload/formulários e de tentativas de login (5 por conta ou 30 por IP em 15 minutos). Sessões duram até 8 horas; “Lembrar de mim” dura 7 dias, sujeito à revogação por versão de autenticação.

Registros de auditoria contêm autor, ação, entidade, identificador e horário UTC; não armazenam cópias de documentos, senhas ou tokens. O esquema e o mecanismo de backup foram preparados para SQLite. Uma implantação com maior concorrência requer avaliação própria.

## Organização

| Caminho | Responsabilidade |
| --- | --- |
| `uairotas/__init__.py`, `config.py` | Aplicação, configuração, segurança e comandos |
| `models.py`, `migrations.py` | Entidades e evolução do banco |
| `validation.py`, `fleet_service.py` | Validações e regras de cadastro |
| `analytics.py` | Filtros, indicadores e alertas compartilhados |
| `auth.py`, `users.py`, `main.py` | Rotas HTTP |
| `demo.py` | Dados fictícios opcionais |
| `templates/` | Páginas e componentes Jinja |
| `static/css/` | Identidade visual e componentes |
| `static/js/core.js` | Estado de áudio, armazenamento e geometrias |
| `static/js/app.js`, `maps.js` | Interações e mapa |
| `tests/` | Testes Python e JavaScript |

## Limites e próximos passos

A [IMPLEMENTACAO_REVISAO.md](IMPLEMENTACAO_REVISAO.md) relaciona o que foi aplicado e o que continua pendente. Restam a validação visual em navegadores reais, a integração autenticada Cobli/IXC e a avaliação da implantação. O token do Mapbox é configurado localmente e não acompanha o código versionado. Credenciais secretas, bancos da empresa e configurações privadas também ficam fora do repositório.

Referências técnicas: [Flask — segurança](https://flask.palletsprojects.com/en/stable/web-security/), [Mapbox — preservar camadas ao trocar estilo](https://docs.mapbox.com/mapbox-gl-js/example/style-switch/), [Mapbox — desempenho](https://docs.mapbox.com/help/troubleshooting/mapbox-gl-js-performance/) e [WCAG 2.2 — contraste](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
