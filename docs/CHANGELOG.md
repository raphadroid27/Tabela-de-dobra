# Changelog

Histórico de mudanças do aplicativo Cálculo de Dobras

## 2.1.0 (15/07/2025)

- Melhora a responsividade e o layout da interface, ajustando tamanhos de janelas, cabeçalhos, espaçamentos e margens.
- Atualiza e personaliza barras de título e menus, incluindo exibição do nome do usuário no login.
- Refatora componentes da UI para melhor organização e experiência visual.

## 2.0.1 (14/07/2025)

- Adiciona estilos personalizados para tooltips no módulo de estilo

## 2.0.0 (14/07/2025)

- Interface totalmente renovada, com visual mais moderno, responsivo e novos ícones para facilitar a identificação das funções.
- Agora é possível escolher entre tema escuro, claro ou automático diretamente no menu Opções, proporcionando mais conforto visual em diferentes ambientes.
- Formulários e campos foram reorganizados para tornar a navegação mais intuitiva, com botões e elementos melhor posicionados e atalhos de teclado otimizados.
- Diversos ajustes visuais deixam a leitura dos dados mais clara, com fontes maiores, espaçamentos aprimorados e rótulos mais explicativos.
- O desempenho geral do sistema foi aprimorado, tornando o uso mais rápido e estável, além de reduzir erros e travamentos.

## 1.2.0 (01/07/2025)

- Adicionado formulário de impressão em lote com funcionalidades de seleção de diretório e lista de arquivos  
- Melhorada a busca de arquivos PDF ao extrair a parte principal do nome
- Alterada as cores dos botões para tons mais claros (botão "Resetar Senha" para amarelo claro, botão "Procurar" para cinza claro)
- Melhorada a estabilidade geral da interface com correções de erros internos

## 1.1.4 (27/06/2025)

- Adicionados novos campos numéricos (valor dedução, largura, altura, etc.) para aceitarem "," como separador de casas decimais.
- Corrigidos erros de codificação e inconsistências em mensagens e comentários.
- Melhorada a atualização dos comboboxes de dedução com valores distintos e filtrados.
- Adicionadas verificações para evitar erros ao acessar widgets na atualização da interface principal.
- Melhorada a verificação de inicialização de widgets e variáveis antes do acesso aos seus valores.
- Reorganizada a lógica de carregamento da interface e move funções de limpeza para um novo módulo.

## 1.1.3 (27/05/2025)

- Melhorada a clareza e funcionalidade dos eventos nos widgets do cabeçalho.
- Corrigida a consulta de materiais para garantir nomes corretos.
- Ajustada a lógica de fechamento da janela de autenticação para evitar erros.
- Otimizada a inicialização e configuração de formulários e listas.
- Corrigido o cálculo de toneladas por metro considerando espessura, material e canal.
- Melhorada a legibilidade e organização do código em diversos módulos.
- Atualizado o script de versão para preservar conteúdos existentes.

## 1.1.2 (23/05/2025)

- Melhorada a formatação do changelog para maior legibilidade.
- Scripts de adição de dados (carbono, H14 e inox) reorganizados e renomeados com prefixo 'add'.
- Melhorada a busca nas configurações com validação de itens vazios.
- Simplificada a atualização de valores no combobox de dedução de canal.

## 1.1.1 (15/05/2025)

- Ordena a lista de materiais pelo nome e ajusta a listagem de itens no formulário de materiais

## 1.1.0 (13/05/2025)

- Criado menu 'Ferramentas' e adicionado o atalho 'Razão Raio/Espessura'.
- Adicionado formulário para cálculo da razão entre raio interno e espessura, com barra de rolagem na tabela de resultados e aviso sobre uso de valores teóricos.
- Incluída limpeza automática do valor no formulário de cálculo da razão entre raio interno e espessura ao limpar campos.
- Realizados ajustes de desempenho e organização interna do código (sem impacto direto no uso).

## 1.0.4 (07/05/2025)

- atualiza o caminho do arquivo CHANGELOG.md para a pasta de documentação
- permite navegação com a tecla Enter nas entradas de dobras
- altera 'i' para 'row' no cálculo do blank
- define foco pós-limpeza de campos
- ajusta obtenção de ícone do aplicativo
- transfere arquivos de licença e changelog para documentação do projeto

## 1.0.3 (06/05/2025)

- Ajusta a conversão de dedução específica para aceitar vírgulas como separador decimal
- Corrige a conversão do raio interno para aceitar vírgulas como separador decimal

## 1.0.2 (05/05/2025)

- Centraliza a lógica de obtenção do caminho do ícone em uma função dedicada
- Refatora a função editar para que atualize a lista de exibição automaticamente após a alteração de um item

## 1.0.1 (30/04/2025)

- ajusta verificação de permissão no formulário de gerenciamento de usuários
- atualiza a função obter_configuracoes para usar lambdas e melhorar a legibilidade dos valores
- modifica cabecalho.py para centralizar o conteúdo da label observações

## v1.0.0 - Otimizações Finais (28/04/2025)

- Refatoradas funções de atualização de widgets para melhor consistência
- Otimizado código para melhor desempenho geral
- Melhorada a legibilidade do código em funções críticas
- Corrigido comportamento de widgets em diferentes resoluções de tela
- Finalização do projeto com estabilidade para uso em produção
- Versão oficial pronta para distribuição

## v0.6.0 - Renovação de Funcionalidades (22/04/2025)

- Renomeado diretório de configuração para "Cálculo de Dobra"
- Atualizada descrição do projeto no README.md
- Modificada configuração de widgets Treeview para melhor exibição de dados
- Atualizado título e versão no formulário "Sobre"
- Aprimorado tratamento de papéis de usuário na criação de contas
- Corrigido sistema de avisos sobre módulos ausentes
- Removida conversão redundante de PNG para ICO
- Refatorado código para melhorar legibilidade e manutenção

## v0.5.0 - Reestruturação do Projeto (17/04/2025)

- Completa reestruturação do projeto com organização em diretórios (src, assets, database)
- Definido caminho absoluto para melhor gestão do banco de dados
- Atualizado sistema de ícones com tratamento para diferentes ambientes
- Refatorada a classe ToolTip para melhor comportamento visual
- Melhorado sistema de associação de eventos em widgets
- Adicionada funcionalidade de expansão vertical e horizontal da interface
- Implementado sistema de verificação de aba mínima no cálculo de dobras
- Ajuste na largura das colunas de dobra para melhor visualização

## v0.4.0 - Refatoração e UX (02/04/2025)

- Adicionado sistema completo de tooltips para melhorar usabilidade
- Implementada classe Tooltip para exibir informações ao passar o mouse
- Criada função PlaceholderEntry para gerenciar textos temporários
- Refatorado sistema de navegação por teclas direcionais nos campos
- Melhorada a tratativa de exceções e mensagens de erro
- Adicionado módulo de avisos com mensagens relacionadas ao corte a laser
- Implementado sistema de logs para registro de ações no banco de dados

## v0.3.0 - Sistema de Autenticação (19/02/2025)

- Adicionado sistema completo de autenticação de usuários com hash de senha
- Implementado gerenciamento de usuários (criação, edição, exclusão)
- Criado mecanismo de proteção para o usuário administrador
- Introduzido sistema de papéis de usuário (admin/usuário comum)
- Adicionada funcionalidade para resetar senhas de usuários
- Implementada verificação de permissões para operações sensíveis
- Refatoradas funções de edição para utilizar parâmetros dinâmicos
- Reorganizada a lógica de posicionamento de janelas na interface

## v0.2.0 - Interface e Formulários (13/02/2025)

- Implementado formulário "Sobre" com informações do aplicativo
- Melhorada ordenação de espessuras por valor numérico
- Adicionadas funcionalidades de busca em tempo real
- Implementadas operações CRUD para espessuras, materiais e canais
- Refinada a lógica de validação de entrada de dados
- Adicionada formatação de exibição para duas casas decimais
- Implementado sistema de filtragem em formulários de materiais e canais

## v0.1.0 - Lançamento Inicial (18/12/2024)

- Commit inicial do projeto de cálculo de dobras
- Configuração básica de diretórios e arquivos
- Implementação inicial do banco de dados SQLite
- Estruturação de módulos para funcionamento básico da aplicação
- Criação dos primeiros componentes da interface gráfica
- Adicionados arquivos iniciais de dados para dobras

