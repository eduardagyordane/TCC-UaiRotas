# Resultados dos testes — revisão UaiRotas

Execução final: **25/09/2026**, Linux, Python **3.12.14** e Node.js **24.19.0**.

## Resultado

| Verificação | Resultado |
| --- | --- |
| Pytest — backend, rotas HTTP, banco e templates | **126 aprovados**, 41,64 s |
| Node — comportamento de áudio, armazenamento e mapa simulado | **12 aprovados**, 0,11 s |
| Total | **138 testes aprovados** |
| Cobertura Python combinada de instruções e ramificações | **94,11%** (arredondada para 94% no terminal) |
| Instruções Python cobertas | 1.136 de 1.191 — 95,38% |
| Ramificações cobertas | 318 de 354 — 89,83% |
| JavaScript dos controladores de mapa e áudio | Carregado e exercitado pelos 12 testes Node |
| `git diff --check` | Sem erro após ajuste de espaço em branco |

A execução emitiu um aviso de depreciação de `datetime.utcnow()` dentro de Flask-Login 0.6.3, no teste de “Lembrar de mim”. Nenhum teste falhou. O aviso pertence à dependência; não foi ocultado nem foi alterado o código instalado dela.

## O que foi exercitado

**Persistência e cálculos:** veículo/motorista com vínculo; os cinco tipos de lançamento financeiro; centavos e litros fracionados; idempotência de envio; leitura cronológica de odômetro; datas inválidas/futuras; vínculos inexistentes; números negativos, não finitos ou com precisão excessiva; edição e auditoria; fotos válidas/falsas; conclusão de manutenção com custo efetivo.

**Usuários e autenticação:** criação e edição de todos os dados; validação de telefone/e-mail/CPF/nascimento/função/senha; duplicidades; dados preservados em erro sem repopular senha; paginação; consulta de detalhes; permissões de supervisor; proteção do último administrador por HTTP e por SQL; senha atual no perfil; revogação de sessão e de cookie persistente; redirecionamentos maliciosos rejeitados; limite de tentativas.

**Relatórios e rotas:** filtros de colaborador/situação/data aplicados às listas e aos dados do mapa; intervalo inclusivo; exclusão de despesas fora do período e manutenções agendadas; conciliação dos totais entre cartões, categorias, veículos, colaboradores e séries; CSV com os mesmos totais e proteção contra fórmulas; média ponderada do combustível; tempos; distância zero; estados sem dados.

**Separação e novos filtros dos relatórios:** conteúdo próprio de Resumo/Frota/Rotas; veículo e motorista, isolados ou combinados com período; manutenção e lançamentos filtrados; paginação sem repetição; seleção preservada entre abas e CSV; IDs inexistentes ou inválidos recusados no HTML e na exportação; totais históricos preservados após troca do motorista atual do veículo; tratamento explícito de gastos/OS sem vínculo; cadastro e edição do motorista em abastecimentos. A migração 2 foi executada duas vezes sobre um esquema anterior e preservou OS reais sem inventar seu veículo; os vínculos demonstrativos inequívocos foram preenchidos.

**Configuração Mapbox:** a versão preparada para publicação lê o token de `MAPBOX_ACCESS_TOKEN` no ambiente ou no `.env` local. A inclusão do token nos arquivos versionados foi removida após bloqueio pela proteção de segredos do GitHub. Os testes das páginas de mapa utilizam um valor sintético e não validam autorização, saldo, cotas ou resposta do provedor.

Após esse ajuste de configuração, foram repetidos os testes de Mapbox, Home, Rotas e segurança: **42 aprovados em 10,44 s**. O token local foi conferido e seu valor estava ausente dos arquivos destinados à publicação.

**Mapa e áudio:** execução do JavaScript real do mapa com um objeto substituto para Mapbox/fetch, verificando preservação de geometria após trocar tema, manutenção do foco, restauração de marcadores, falha/repetição de Directions e cancelamento por timeout. Controladores de áudio exercitados com autoplay bloqueado, erros de reprodução, eventos diferentes, deduplicação entre páginas, preferências por usuário, reprodução concorrente e silenciamento durante uma tentativa pendente.

**Operação e apresentação:** migração preserva usuário antigo e pode ser repetida; backup consistente e sem sobrescrita; CSRF e limite de upload; produção exige segredo/hosts; domínio recusado retorna 400; cabeçalhos; links internos das páginas retornam 200; diálogos têm rótulos existentes; Mapbox carregado apenas nas páginas com mapa; arquivo sonoro preservado.

## Medição isolada de Usuários

Medição da revisão anterior, **antes desta alteração de relatórios**, não repetida nesta entrega. Com **1.001 contas sintéticas**, consulta autenticada, SQLite em memória, uma execução de aquecimento e mediana de cinco GETs:

| Medida | Valor |
| --- | --- |
| Linhas de usuários na primeira página | 25 |
| Diálogos de cadastro/edição de usuário | 1 |
| HTML da resposta, sem compressão | 16.536 bytes |
| Mediana do GET | 2,51 ms |

Essa medição comprova que o HTML não contém um formulário para cada uma das 1.001 contas. Ela **não mede** rede, pintura, memória do navegador, concorrência ou banco em disco e não representa uma promessa de tempo de carregamento em produção.

## Arquivo sonoro preservado

- Tamanho: **304.128 bytes**.
- SHA-256: `9dbd60f923d88fc74d2903edebebae2aaeb99ce1edf9feff0dfd2f76ce205221`.
- O teste compara o arquivo com esse valor fixo e funciona também no pacote ZIP, sem depender da pasta Git.

## Limites desta verificação

- Não foram usados dados pessoais, credenciais operacionais ou bancos da empresa.
- Não houve chamada real às APIs Cobli/IXC ou Directions/Mapbox durante os testes.
- Os objetos simulados de Mapbox e áudio **não substituem** WebGL e políticas de reprodução dos navegadores.
- O navegador disponível recusou o endereço local com `ERR_BLOCKED_BY_CLIENT`. Permanecem pendentes a revisão renderizada de todas as telas, os cliques/teclado em navegador real, celular, zoom de 200%, contraste final, áudio real e desempenho de rede.
- A cobertura acima se refere ao Python. Não é um percentual de cobertura da experiência visual completa, da segurança de uma implantação ou das APIs externas.
- Dependências foram fixadas nas versões usadas; não foi executada uma varredura de vulnerabilidades nem teste de carga da implantação.
- Os números acima são da execução local. O fluxo de GitHub Actions executa os testes em pushes e pull requests; os resultados remotos ficam disponíveis na aba Actions do repositório.

## Reproduzir

Instale `requirements-dev.txt` no ambiente virtual e execute:

~~~bash
python -m pytest -q --cov=uairotas --cov-report=term-missing
node --test tests/frontend/core.test.cjs tests/frontend/maps.test.cjs
~~~

O README contém os caminhos completos dos executáveis para Windows, Linux e macOS.
