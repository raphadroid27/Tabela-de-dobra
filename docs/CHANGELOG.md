# Changelog

Histórico de mudanças do aplicativo Calculadora de Dobras

## 2.6.0 (04/12/2025)

- refatora: reestrutura módulos de conversão separando lógica de negócio da interface
- refatora: adiciona atalho de teclado F1 para abrir o manual de uso na ferramenta administrativa
- refatora: adiciona atalho de teclado F1 ao manual de uso no menu de ajuda
- refatora: ajusta a largura da janela de autenticação para 210 pixels
- refatora: adiciona atalhos de teclado para adicionar arquivos nas listas do comparador
- refatora: atualiza conteúdo de ajuda com melhorias nos atalhos e informações sobre a ferramenta administrativa
- refatora: adiciona persistência da geometria da janela administrativa e melhora a seleção de itens
- refatora: implementa monitoramento de inatividade para a ferramenta administrativa e formulário de autenticação
- refatora: simplifica o módulo de autenticação e melhora a gestão de janelas
- refatora: adiciona ajuda contextual para os formulários de cadastro, inclusão e edição
- refatora: adiciona atalhos de ajuda em várias páginas de conteúdo
- refatora: melhora módulos de conversão DWG e PDF para tratamento de erros e organização de código.
- refatora: adiciona suporte à conversão DWG para DWG 2013 e implementa opção de substituição do arquivo original
- refatora: adiciona novos ícones SVG e ajusta estilos de componentes para suporte a temas claro e escuro
- refatora: remove funções obsoletas de estilo e reorganiza a aplicação de estilos CSS
- refatora: ajusta estilos de QComboBox e QMenu, melhorando a formatação e a aparência
- refatora: ajusta ícones de verificação e implementa suporte a tema claro e escuro
- refatora: ajusta função get_widgets_styles para aceitar tema como parâmetro
- refatora: adiciona ícone de verificação e ajusta estilos de indicadores em QMenu e QCheckBox
- refatora: ajusta estilos de widgets, adicionando seletores e melhorando a formatação
- refatora: ajusta altura do formulário de impressão e define tamanho padrão no manual
- refatora: ajusta estilos de widgets, alterando alturas mínimas e tamanho da fonte
- refatora: simplifica mensagem de cópia e ajusta temporizador, além de aplicar cores dinâmicas na força
- refatora: ajusta limites de tamanho da janela e melhora layout da tabela
- refatora: altera modo de seleção das tabelas para seleção única
- refatora: ajusta altura dos formulários de comparação e conversão para melhor layout
- refatora: melhora tratamento de exceções e simplifica lógica de fallback em utilitários
- refatora: adiciona atalhos de teclado para ajuda em vários formulários
- refatora: ajusta estilos e dimensões de formulários para melhor consistência e layout
- refatora: altera títulos de seções de <h2> para <h4> para consistência no formato de ajuda
- refatora: ajusta tamanhos de formulários utilizando constantes para melhor manutenção
- refatora: ajusta alturas de janelas e componentes para melhor layout
- refatora: ajusta layout e dimensões do formulário de impressão
- refatora: ajusta formatação de flags de janela e normaliza código
- refatora: ajusta tamanhos de janelas e configura redimensionamento mínimo
- refatora: altera o redimensionamento do diálogo para ajustar o tamanho mínimo
- refatora: ajusta tamanhos fixos e margens na janela de autenticação
- refatora: normaliza textos em mensagens de diálogo e ajusta fallback para mensagens vazias
- refatora: altera redimensionamento da janela principal para tamanho fixo
- refatora: renomeia função de configuração de janelas para português
- refatora: ajusta estilos de widgets para utilizar paletas de cores dinâmicas
- refatora: altera tamanhos fixos para tamanhos mínimos em várias janelas e formulários
- refatora: ajusta a largura mínima dos estilos de widgets para permitir flexibilidade
- refatora: ajusta a altura de várias janelas e formulários para 500
- refatora: remove a versão do título da janela principal
- refatora: implementa gerenciamento de estado da janela e otimiza o carregamento de temas
- refatora: adiciona suporte para menus compactos e gerenciamento de eventos de redimensionamento
- refatora: adiciona suporte para cores de destaque e aprimora gerenciamento de temas
- refatora: adiciona estilos personalizados para QMenuBar e QMenu
- refatora: ajusta estilos de QTableWidget e QLabel para utilizar paletas de cores
- refatora: ajusta estilos de QGroupBox e QLabel para remover bordas e padronizar rótulos
- refatora: renomeia objetos de título para label_titulo em diversos formulários e componentes
- refatora: ajusta componentes de interface e implementa gerenciamento centralizado de tema
- refatora: remove gerenciamento de temas qdarktheme e ajusta estilos de widgets
- refatora: remove a barra de título customizada e ajusta janelas para usar a barra de título nativa
- recurso: adiciona requerimentos de desenvolvimento ao arquivo requirements.txt
- recurso: adiciona script para adicionar dados de espessura, canal e dedução de materiais ao banco de dados
- refatora: remove arquivos obsoletos e scripts de adição de materiais do banco de dados
- refatora: adiciona função show_timed_message_box para exibir mensagens com timeout e atualiza o fechamento do aplicativo
- refatora: ajusta diretório de runtime para incluir subpasta 'calculadora_dobra'
- recurso: adiciona script para geração automática de picks em arquivos DXF

## 2.5.0 (10/10/2025)

- Refatorações gerais de janelas e UI: fechamento seguro de janelas dependentes, suporte a janelas sem borda e de sistema, melhor posicionamento, ajustes de tamanhos/atributos de formulários e seleção estendida em tabelas.
- Ajuda e manual: conteúdos HTML externos, exibição otimizada do manual, ajuda contextual integrada a vários formulários e melhoria da legibilidade/estrutura da documentação de uso.
- Conversão e comparação de arquivos: novos formulários e menu para comparação geométrica (STEP) e conversão (PDF↔DXF via Inkscape, DWG→PDF em duas etapas), tratamento de erros, cancelamento, atalhos e reordenação de botões.
- Usabilidade e estilo: novos atalhos e tooltips, cor de botão laranja com estados, estilos aplicados a tabelas (QTableWidget), melhorias de responsividade e acessibilidade de teclado.
- Dependências e build: atualização de requirements (pillow, matplotlib, ezdxf, PyMuPDF, PyQtDarkTheme-fork), remoção de scripts obsoletos e atualização de versão.
- Performance, cache e banco: implementação de cache com persistência/invalidação, otimização de timeouts, validações de integridade (limpeza de deduções órfãs) e simplificação da gestão de instâncias.
- Limpeza e manutenção: renomeações, padronização de imports/docstrings, remoção de dependências e de código legado, e aprimoramentos gerais de legibilidade e organização do projeto.

## 2.4.1 (02/09/2025)

- Refatorações gerais para melhorar segurança, legibilidade e organização do código:
    - Comentário de segurança na importação do subprocess.
    - Ajuste de formatação em tooltips.
    - Simplificação da busca de deduções usando função dedicada.
    - Remoção de parâmetro não utilizado em set_sqlite_pragma.
    - Encapsulamento da lógica de busca de dedução e obtenção de usuário logado.
    - Habilitação de ordenação por coluna e cores alternadas nas listas.
    - Atualização do gerenciamento de sessões do banco de dados.

## 2.4.0 (29/08/2025)

- Implementado gerenciamento de IPC e simplificado o registro de sessões, removendo dependências do banco de dados
- Refatoração geral para simplificação e padronização do código, incluindo melhorias na lógica de autenticação, gerenciamento de usuários, interface, layout e estilo dos widgets.
- Remoção de funções, módulos, variáveis e arquivos obsoletos para facilitar manutenção e reduzir complexidade.
- Adição de funcionalidades: gerenciamento de usuários, módulo de administração, suporte à transparência de janelas, gerenciamento de instâncias e argumentos de linha de comando.
- Centralização e aprimoramento de mensagens, logs, estilos de botões e configurações de interface.
- Otimização de timers, importações, tipagem, validações de segurança e tratamento de erros.
- Atualização de documentação, instruções de execução e arquivos de configuração.
- Renomeação do aplicativo para "Calculadora de Dobra" e ajustes visuais em diversos componentes.
- Melhoria na organização do código, legibilidade, consistência e desempenho geral do sistema.

## 2.3.1 (31/07/2025)

- Melhorada a lógica de verificação de atualizações e gerencia a versão instalada no banco de dados

## 2.3.0 (31/07/2025)

- Novo sistema de atualização automática integrado ao aplicativo, permitindo verificar e instalar novas versões diretamente pela interface, com barra de progresso e notificações aprimoradas.
- Adicionado módulo de gerenciamento de atualizações, facilitando o download e aplicação de updates sem necessidade de reinstalação manual.
- Implementado sistema de logging para melhor rastreamento de erros e eventos, aumentando a confiabilidade e facilitando o suporte.
- Melhorias na interface de autenticação, incluindo integração à janela principal, ajustes visuais e novo botão de recarregar na barra de título.
- Diversas refatorações para maior estabilidade, clareza do código e melhor gerenciamento de sessões.

## 2.2.0 (21/07/2025)

- Refatoração geral do código para melhorar modularidade, clareza e manutenção, incluindo:
    - Centralização e simplificação da lógica de cálculo e atualização da interface.
    - Introdução e reorganização de módulos utilitários, controladores e gerenciadores de widgets.
    - Renomeação e padronização de funções e métodos para maior consistência.
    - Implementação de classes para limpeza de campos e gerenciamento de cópia/listagem.
    - Otimização do tratamento de erros e atualização de documentação.
    - Backup e reorganização de arquivos e pastas legadas.
- Ajustes em importações e remoção de módulos obsoletos.
- Melhorias na gestão e posicionamento de janelas da interface.
- Adicionado suporte à detecção de tema do sistema e atualiza a lógica de mudança de tema

## 2.1.1 (15/07/2025)

- Exibe dicas explicativas (tooltips) na validação da aba mínima para facilitar o preenchimento.
- Ajustados estilos de tooltip e formatação de texto em widgets
- atualizados rótulos de força para incluir unidade [Ton/m] no cabeçalho e no formulário universal

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

