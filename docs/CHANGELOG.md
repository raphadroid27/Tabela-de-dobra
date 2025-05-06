# Changelog

Histórico de mudanças do aplicativo Cálculo de Dobras

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

- Extensas correções de código baseadas em padrões Pylint
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
- Adicionada versão "0.1.0-beta" no formulário "Sobre"
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

