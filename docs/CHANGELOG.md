# Changelog

Histórico de mudanças do aplicativo Cálculo de Dobras

## 2.0.0 (04/07/2025)

- melhora: adiciona chamada à função buscar nas operações de adicionar e excluir
- melhora: refatora o código para melhorar a legibilidade e a estrutura das funções de adição e exclusão
- melhora: refatora o código para melhorar a legibilidade e tratamento de exceções nas funções de atualização de widgets
- melhora: refatora o código para melhorar a legibilidade e a estrutura do aplicativo
- melhora: adiciona desativação de avisos específicos no pylint e configurações de formatação no VSCode
- recurso: implementa análise e otimização de uso de widgets globais
- melhora: simplifica a lógica de atualização dos comboboxes e melhora a preservação de estados
- melhora: adiciona controle para atualização automática dos comboboxes de dedução e evita buscas desnecessárias
- melhora: atualiza ações do menu para usar setattr em vez de form_false
- melhora: remove uso de tooltips personalizados e substitui por tooltips nativos do PySide6
- melhora: remove altura fixa dos avisos para permitir ajuste dinâmico
- melhora: corrige o comando de execução do programa principal no README.md
- melhora: refatora ações do menu para simplificar a lógica de edição e remove prints de debug
- melhora: aprimora funções de cálculo de dobras, adicionando segurança na atualização de widgets e refinando a lógica de dedução
- melhora: refatora atualização de comboboxes de materiais e dedução, removendo código redundante
- melhora: remove mensagens de log desnecessárias ao capturar estado dos widgets
- melhora: remove comentários desnecessários
- melhora: centraliza a limpeza de janelas órfãs utilizando função dedicada
- remove: exclui formulários obsoletos de canal, dedução, espessura e material
- melhora: remove seleção inicial dos comboboxes de espessura e canal ao atualizar
- melhora: atualiza chamadas para calcular_valores após alterações em materiais, espessuras, canais e deduções
- melhora: adiciona navegação por teclado nas entradas de dobras e corrige foco para setFocus
- melhora: evita execução de busca CRUD durante recarregamento da interface usando flag de controle
- refatora: migra canal_tooltip para tooltip nativo do PySide6 e remove chamadas redundantes em todas_funcoes
- organiza: centraliza tooltips do cabeçalho e implementa tooltip automático para combobox de canais
- melhora: aprimora aviso do formulário de razão R/E com QTextBrowser justificado e sem barras de rolagem
- refatora: substitui placeholder manual por nativo e usa QTextBrowser para exibição somente leitura no formulário de impressão
- melhora: aprimora limpeza de janelas órfãs preservando formulários ativos durante expansão da interface
- adiciona: implementa flag INTERFACE_RELOADING para evitar recarregamentos indesejados durante expansão da interface
- refatora: atualiza botões com ícones e estilos modernos para melhorar a interface
- refatora: substitui função no_topo por aplicar_no_topo e aprimora lógica de gerenciamento de janelas
- remove: exclui arquivos de teste obsoletos após reorganização do projeto
- corrige: corrige layout quebrado após expansão/contração da interface
- refatora: melhora a função de autenticação com novos estilos de botão e ajustes na janela modal
- refatora: aprimora função copiar e integração com formulário universal
- corrige: migra sistema CRUD completamente para PySide6 e resolve problemas de adição de itens
- refatora: ajusta formulários em uma estrutura universal para melhorar a manutenção e organização
- refatora: ajusta margens, espaçamentos e alturas fixas nos componentes da interface
- refatora: atualiza e remove arquivos de banco de dados obsoletos
- refatora: migração completa para pyside6
- corrige: fórmula do fator k e atualiza lógica de aplicação
- refatora: remove sistema legado de salvamento/restauração de widgets
- recurso: integrar sistema de estado de widgets no gerenciador de interface
- recurso: implementa sistema centralizado de gerenciamento de estado de widgets
- refatora: reescreve logica de exibicao das comboboxes do cabecalho
- refatora: otimiza estrutura do projeto e melhora organização
- inicial
- build: lançamento da versão 1.2.0 com novas funcionalidades e melhorias
- corrige: resolve problema das funções expandir vertical e horizontal não funcionarem
- refatora: altera a cor do botão "Resetar Senha" para amarelo claro na interface gráfica
- refatora: altera a cor do botão "Procurar" para cinza claro na interface gráfica
- refatora: adiciona limpeza de formatação de código e melhoria da legibilidade em múltiplos arquivos
- refatora: altera cores dos botões para tons mais claros na interface gráfica
- refatora: melhora a busca de arquivos PDF ao extrair a parte principal do nome
- refatora: adiciona verificações de existência para widgets antes de manipulação no formulário de impressão
- refatora: atualiza o arquivo tabela_de_dobra.db com novas alterações
- refatora: remove importações desnecessárias e melhora a formatação do código no formulário de impressão
- refatora: melhora a função de seleção de diretório com habilitação e desabilitação de janelas
- recurso: adiciona formulário de impressão em lote com funcionalidades de seleção de diretório e lista de arquivos
- build: atualiza para a versão 1.1.4 com novas funcionalidades e melhorias
- refatora: adiciona novos campos numéricos na função de processamento de edição
- corrige: ajusta erros de codificação e inconsistências em mensagens e comentários
- refatora docstrings para usar aspas duplas para consistência em todos os módulos
- corrige: corrigir erros de Pylint e problemas de encoding
- refatora: melhora a atualização dos comboboxes de dedução com valores distintos e filtrados
- refatora: adiciona verificações para evitar erros ao acessar widgets na atualização da interface
- refatora: adiciona verificações para evitar erros ao acessar a interface principal
- refatora: melhora a verificação de inicialização de widgets e atualiza o cálculo de valores
- refatora: melhora a verificação de inicialização das variáveis antes de acessar seus valores
- corrige: ajusta erros de acesso a atributos None e problemas de formatação
- refatora: reorganiza a lógica de carregamento da interface e move funções de limpeza para um novo módulo
- refatora: atualiza os arquivos da tabela de dobra no banco de dados

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

- Commit inicial do projeto de Cálculo de Dobras
- Configuração básica de diretórios e arquivos
- Implementação inicial do banco de dados SQLite
- Estruturação de módulos para funcionamento básico da aplicação
- Criação dos primeiros componentes da interface gráfica
- Adicionados arquivos iniciais de dados para dobras

