# Resultado dos testes

Execução realizada em 18 de setembro de 2026 com Python 3.12.14.

```text
......................                                                   [100%]
22 passed in 3.91s
Cobertura total: 91%
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
