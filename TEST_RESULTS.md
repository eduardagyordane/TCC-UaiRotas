# Resultado dos testes

Execução realizada em 23 de setembro de 2026 com Python 3.12.14.

```text
...................................................................      [100%]
72 passed in 12.70s
Cobertura total: 96%
```

## Casos verificados

- Carregamento da tela de login.
- Redirecionamento de visitantes para o login.
- Autenticação com credenciais válidas.
- Mensagem genérica para credenciais inválidas.
- Redirecionamento de usuário já autenticado.
- Encerramento da sessão.
- Rejeição de redirecionamento para domínio externo.
- Armazenamento seguro da senha por hash.
- Proteção da Home contra acesso sem autenticação.
- Renderização dos indicadores operacionais.
- Renderização das ordens de serviço demonstrativas.
- Exibição do alerta de almoço superior a duas horas.
- Presença dos controles acessíveis de tema e navegação.
- Presença do formulário protegido para encerrar a sessão.
- Proteção do módulo de Rotas contra acesso sem autenticação.
- Renderização do mapa, colaboradores e ordens de serviço.
- Exibição de cliente, endereço e tipo de serviço.
- Exibição dos locais de interesse e do alerta de almoço.
- Filtro de ordens por colaborador.
- Filtro de ordens por situação.
- Estado vazio quando nenhuma ordem corresponde aos filtros.
- Navegação da Home para o módulo de Rotas.
- Proteção do módulo de Frotas contra acesso sem autenticação.
- Renderização do resumo, veículos, custos e manutenções da frota.
- Exibição das datas e alertas de troca de óleo.
- Presença dos sete formulários de inclusão da frota.
- Registro validado de veículo, motorista, troca de óleo, abastecimento, multa, gasto e manutenção.
- Rejeição dos formulários sem campos obrigatórios.
- Retorno 404 para tipos de registro desconhecidos.
- Navegação da Home para o módulo de Frotas.
- Proteção das três telas de Relatórios contra acesso sem autenticação.
- Renderização do resumo geral e dos gráficos operacionais.
- Navegação para os relatórios detalhados de Rotas e Frotas.
- Exibição dos custos, consumo e manutenção por veículo.
- Exibição da produtividade, tempos, desvios e alerta de almoço por colaborador.
- Seleção dos períodos de 7, 30 e 90 dias e do ano de 2026.
- Retorno seguro ao período de 30 dias quando o filtro é inválido.
- Navegação da Home para o módulo de Relatórios.
- Proteção do módulo de Usuários contra visitantes e supervisores.
- Renderização do resumo, tabela, busca e formulários de usuários.
- Cadastro persistente com todos os campos pessoais solicitados.
- Armazenamento da senha somente por hash.
- Validação de CPF, função, data de nascimento, senha, e-mail e CPF duplicados.
- Edição completa dos dados pessoais, função, situação e senha opcional.
- Proteção contra a desativação do próprio administrador autenticado.
- Busca por nome, e-mail e CPF.
- Atualização segura de bancos criados antes do módulo de Usuários.
- Navegação da Home para o módulo de Usuários.
- Carregamento dos contêineres do Mapbox na Home e em Rotas.
- Inclusão segura da chave por variável de ambiente.
- Serialização de rotas, veículos, ordens e locais de interesse.
- Carregamento do Mapbox GL JS com tratamento de token e erro.
- Ajuste das rotas à malha viária pela Directions API, com fallback em GeoJSON.
- Disponibilidade e assinatura válida do arquivo MP3 de alerta.
- Controle para ativar ou silenciar alertas sonoros.
- Reprodução única por alerta durante a sessão e fallback para bloqueio de autoplay.
- Disparo sonoro para alertas operacionais e eventos recebidos em tempo real.
