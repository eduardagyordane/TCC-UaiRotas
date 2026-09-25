# Aplicação da revisão de UaiRotas

Data: 25/09/2026. Base: relatório de revisão de 24/09/2026. Tecnologias e identidade vinho/vermelho/amarelo foram mantidas.

## Implementado

| Área do relatório | Alterações nesta revisão |
| --- | --- |
| Configuração | Produção recusa chave padrão/exemplo e ausência de hosts; cookies seguros, HSTS, CSP, limite de requisição, CSRF e limite de login |
| Persistência | Veículos, motoristas e seus vínculos; óleo, combustível, multas, outros gastos e manutenções no SQLite |
| Consistência | Dinheiro em centavos, combustível em mililitros, arredondamento decimal e validação cronológica do odômetro |
| Edição da Frota | Edição de cadastros/lançamentos, preservação de leituras históricas e histórico de autor/ação/data |
| Manutenção | Estimativa separada do gasto realizado; conclusão com data e custo efetivos |
| Validação | CPF com dígitos verificadores, telefone/e-mail, datas, limites, números finitos, precisão e vínculos existentes |
| Fotos | Prévia no formulário; tipo real/tamanho/resolução verificados; redimensionamento e remoção de metadados |
| Usuários | Proteção do último admin, paginação de 25 itens, diálogo único, CPF mascarado, dados completos sob autorização |
| Sessão/perfil | Meu perfil; senha atual para mudança de e-mail/senha; revogação de outras sessões e cookies persistentes |
| Filtros | Data, colaborador e situação aplicados a lista/mapa; período, veículo e motorista combinados nos relatórios, com preservação entre abas, paginação e CSV |
| Relatórios | Resumo consolidado, Frota com custos e manutenção, Rotas com atendimentos e deslocamentos; cada tela com conteúdo e gráficos próprios |
| Indicadores | Fonte única para cartões, gráficos, detalhes e CSV; sem números operacionais fixos |
| Gráficos | Custos por categoria/data, gasolina ponderada com eixo zero, custo/km ordenado, produtividade e tempos por colaborador; tabelas alternativas |
| Navegação | Links de OS, central de alertas, perfil, exportação e impressão; remoção de botões e links sem destino |
| Formulários | Valores preservados em erro, senha nunca repopulada, indicação por campo, resumo, diálogo reaberto e foco |
| Mapbox | Geometria preservada no tema, timeout/abort/retry, fallback visível, foco/limpeza, SVGs de interesse e popup completo da OS |
| Áudio | Arquivo original preservado, primeiro desbloqueio corrigido, volume/teste/categorias, IDs globais, reconhecimento por usuário |
| Visual | Texto e botões maiores, cores dos temas revistas, componentes compartilhados, foco visível, layouts móveis e movimento reduzido |
| Desempenho | Mapbox somente nas páginas com mapa, áudio sob demanda, armazenamento protegido, componentes legados removidos e agregações SQL |
| Operação | Migrações aditivas 1 e 2, vínculo histórico de veículo nas OS, backup SQLite sem sobrescrita, auditoria e instruções de atualização |
| Automação | Fluxo de testes para GitHub Actions em pushes e pull requests |

## Decisões e limites

- A base inicia vazia e identifica a origem local. Demonstrações exigem comando explícito e são sinalizadas nas telas.
- Uma rota calculada por Directions foi apresentada como planejada. Nenhum ponto foi anunciado como posição atual ou sincronização real.
- A confirmação de alertas foi separada da resolução: o administrador ou supervisor pode marcar como visto para sua conta, mas o alerta permanece enquanto a regra estiver pendente.
- A edição de uma leitura não altera retroativamente veículo, data ou quilometragem; novas leituras atualizam o odômetro de forma validada.
- Os logs de alterações guardam metadados da ação, não diferenças completas entre valores antigos e novos.
- A data do lançamento de manutenção concluído passa a ser a de realização. Um histórico separado de reprogramações e datas planejadas pode ser acrescentado quando essa necessidade for definida.
- A autorização de Usuários exige papel de admin. A troca de senha pelo próprio usuário exige a senha atual. A redefinição por outro administrador permanece uma ação administrativa auditada.
- Os CSVs exportam o resumo tabular de cada módulo no mesmo intervalo. A impressão/PDF inclui a página e as tabelas alternativas.
- Os filtros dos relatórios usam o motorista/veículo registrado em cada evento. Custos sem motorista e OS sem veículo permanecem nos totais gerais, mas não são atribuídos automaticamente a uma pessoa ou carro. O motorista do lançamento pode ser informado nos formulários de despesas.
- Apenas vínculos inequívocos dos dados demonstrativos antigos são completados pela migração 2. Trocas de motorista no cadastro atual do veículo não reescrevem os relatórios históricos.
- O relatório de Frota lista 25 lançamentos por página; seus totais, gráficos e CSV consideram todos os registros filtrados. A impressão da lista detalhada inclui a página atual.
- A proteção de segredos do GitHub recusou a inclusão do token Mapbox. A configuração usa `MAPBOX_ACCESS_TOKEN` no ambiente ou no `.env` local, sem token embutido nos arquivos versionados. O funcionamento na conta do provedor não foi validado por chamada real.
- O cache de Directions fica na memória da página, além do cache HTTP aplicável; respostas do provedor não foram persistidas no banco.

## Pendências que exigem outra etapa

1. **Navegador real:** conferir cliques, foco, Tab/Shift+Tab/Escape, contraste renderizado, ambos os temas, celular, zoom de 200%, mapas e áudio em Chrome/Firefox/Safari. O acesso ao endereço local foi bloqueado pelo navegador disponível nesta revisão.
2. **APIs:** autenticar Cobli/IXC no backend, mapear IDs, sincronizar incrementalmente, guardar horário real de atualização e calcular ocorrências a partir dos dados operacionais.
3. **Escala:** medir renderização, rede, concorrência, Core Web Vitals e muitos marcadores no ambiente de implantação; considerar camadas/agrupamento e paginação adicional de motoristas caso o volume justifique.
4. **Locais de interesse:** a Frota e o mapa já compartilham os mesmos registros. Uma tela própria de gerenciamento dos locais não fez parte desta revisão.
5. **Operação:** configurar servidor WSGI/proxy/HTTPS, retenção de backups e monitoramento conforme a infraestrutura escolhida.
6. **Central de eventos:** histórico de resolvidos e recebimento em tempo real dependem da sincronização. A central atual reúne ocorrências locais pendentes e reconhecimento por usuário.

As verificações efetuadas e suas limitações estão em TEST_RESULTS.md. A cobertura Python não representa cobertura visual, de rede ou das APIs externas.
