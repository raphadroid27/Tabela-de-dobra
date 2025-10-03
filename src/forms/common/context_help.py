"""Conteúdo centralizado de ajuda contextual para os formulários."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from PySide6.QtWidgets import QWidget

from src.utils.utilitarios import show_info

# pylint: disable=C0301

HelpEntry = Tuple[str, str]
ManualLauncher = Callable[[Optional[QWidget], Optional[str], bool], object]

_manual_launcher: ManualLauncher | None = None

_DEFAULT_ENTRY: HelpEntry = (
    "Ajuda indisponível",
    "Ainda não há instruções contextuais para esta janela.",
)

_HELP_CONTENT: Dict[str, HelpEntry] = {
    "main": (
        "<h2>Tela Principal</h2>",
        "<h3><b>Menu Principal</b></h3>"
        "<p>A barra superior agrupa operações de cadastro, revisão de dados, ferramentas auxiliares e ajustes visuais. Os menus refletem o estado de sessão (ex.: opções de usuário podem ser desabilitadas sem login).</p>"
        "<h4><b>📄 Adicionar</b></h4><ul>"
        "<li><b>➕ Adicionar Dedução / Material / Espessura / Canal</b>: abre formulários em modo inclusão. As combinações alimentam o cálculo no cabeçalho e são recarregadas automaticamente após salvar.</li>"
        "</ul>"
        "<h4><b>✏️ Editar</b></h4><ul>"
        "<li>Acessa os mesmos formulários em modo edição, exibindo botões ✏️ Atualizar e 🗑️ Excluir. A seleção na lista pré-carrega os campos.</li>"
        "</ul>"
        "<h4><b>🔧 Recursos</b></h4><ul>"
        "<li><b>➗ Razão Raio/Espessura</b>: referência de fator K teórico.</li>"
        "<li><b>🖨️ Impressão em Lote</b>: fila e verificação de PDFs.</li>"
        "<li><b>📊 Comparar Arquivos</b>: análise de diferenças por par.</li>"
        "<li><b>🔄 Converter Arquivos</b>: pipelines de conversão multi-formato.</li>"
        "</ul>"
        "<h4><b>👤 Usuário</b></h4><ul>"
        "<li><b>🔐 Login</b> / <b>👥 Novo Usuário</b>: autenticação e criação controlada (primeiro admin auto-detectado).</li>"
        "<li><b>🚪 Sair</b>: encerra sessão e limpa contexto sensível.</li>"
        "</ul>"
        "<h4><b>⚙️ Opções</b></h4><ul>"
        "<li><b>📌 No topo</b> + <b>👻 Transparência</b>: controle de z-order e opacidade vinculados.</li>"
        "<li><b>🎨 Temas</b>: troca persistente, armazenada em config.</li>"
        "</ul>"
        "<h4><b>❓ Ajuda</b></h4><ul>"
        "<li><b>📘 Manual de Uso</b> e <b>ℹ️ Sobre</b>: documentação e metadados.</li>"
        "</ul>"
        "<h4><b>⌨️ Atalhos Globais Principais</b></h4><ul>"
        "<li><kbd>Ctrl+Shift+V</kbd> Expandir linhas • <kbd>Ctrl+H</kbd> Expandir colunas • <kbd>Ctrl+D</kbd> Limpar Dobras • <kbd>Ctrl+T</kbd> Limpar Tudo • Clique em labels azuis/laranja p/ copiar.</li>"
        "</ul>"
        "<h3><b>Cabeçalho (Fluxo de Cálculo)</b></h3>"
        "<ol>"
        "<li><b>Selecionar Material</b>: popula a combo de Espessura apenas com valores que possuem deduções cadastradas (cache + fallback DB).</li>"
        "<li><b>Selecionar Espessura</b>: filtra a combo de Canal conforme a dupla Material/Espessura.</li>"
        "<li><b>Selecionar Canal</b>: busca dedução, força potencial e observações; reseta estilos de campos dependentes.</li>"
        "<li><b>Informar Comprimento</b>: aceita vírgula ou ponto; destaca em vermelho se exceder o limite calculado para o canal/material.</li>"
        "<li><b>Informar Raio Interno</b>: recalcula Fator K/Offset. Fator K: cor <span style='color:orange;'>laranja</span> = teórico (sem canal), <span style='color:blue;'>azul</span> = dedução específica aplicada.</li>"
        "<li><b>Ded. Espec.</b> (opcional): sobrescreve a dedução do banco para aquele cálculo isolado sem alterar o cadastro.</li>"
        "<li><b>Observações</b>: mostra texto associado à dedução vigente (ou vazio se combinação inexistente).</li>"
        "<li><b>Cópia rápida</b>: clique em Fator K, Dedução, Offset para copiar; feedback visual 'Copiado!' desaparece após alguns segundos.</li>"
        "</ol>"
        "<h4><b>Saídas Auxiliares</b></h4><ul>"
        '<li><b>Aba Mín.</b> e <b>Ext. "Z" 90°</b>: exibidas quando as variáveis necessárias estão completas.</li>'
        "<li><b>Força (t/m)</b>: mostra cálculo estimado; campo de comprimento sinaliza limiar excedido em vermelho.</li>"
        "<li><b>Razão RI/E</b>: alimenta janela de referência complementar.</li>"
        "</ul>"
        "<h3><b>Tabela de Dobras</b></h3>"
        "<p>Planilha dinâmica para cada conjunto de abas. Cada linha aceita a <i>Medida Externa</i> e gera <b>Medida Dobra</b> e <b>Metade Dobra</b>; a linha final calcula o Blank total e sua metade.</p>"
        "<ul>"
        "<li><b>Navegação</b>: Enter ou ↓ avança; ↑ retorna; validação dispara recálculo imediato por coluna.</li>"
        "<li><b>Cópia</b>: clique em qualquer resultado (dobra, metade, blank) para enviar ao clipboard.</li>"
        "<li><b>Alerta de Aba Mínima</b>: entradas abaixo do limite são destacadas em <span style='color:white;background:red;padding:1px 3px;'>vermelho</span> para revisão dimensional.</li>"
        "<li><b>Expandir Vertical (Ctrl+Shift+V)</b>: aumenta linhas de 5 para 10.</li>"
        "<li><b>Expandir Horizontal (Ctrl+H)</b>: adiciona nova tabela paralela preservando valores existentes.</li>"
        "<li>🧹 <b>Limpar Dobras</b> (<kbd>Ctrl+D</kbd>): limpa apenas entradas e resultados da(s) tabela(s).</li>"
        "<li>🗑️ <b>Limpar Tudo</b> (<kbd>Ctrl+T</kbd>): limpa cabeçalho + tabelas (reseta contexto completo).</li>"
        "<li><b>Reatividade</b>: qualquer mudança no cabeçalho reprojeta todas as tabelas ativas.</li>"
        "</ul>"
        "<h3><b>Indicadores Visuais</b></h3><ul>"
        "<li><b>Fator K</b> azul = dedução específica; laranja = teórico; normal = dedução padrão.</li>"
        "<li>Comprimento em vermelho = acima do limite permitido para o canal.</li>"
        "<li>Campos de aba em vermelho = abaixo da Aba Mínima calculada.</li>"
        "</ul>",
    ),
    "impressao": (
        "<h2>Impressão em Lote</h2>",
        "<ol>"
        "<li><b>📁 Procurar</b>: escolha o diretório base dos PDFs. O campo ao lado recebe o caminho selecionado ou colado manualmente.</li>"
        "<li>Prepare a entrada textual dos arquivos:<ul>"
        "<li><b>➕ Adicionar</b> (<kbd>Ctrl+Shift+A</kbd>) transfere cada linha digitada no campo <i>Lista de arquivos (um por linha)</i> para a lista organizada.</li>"
        "<li><b>🧹 Limpar Texto</b> (<kbd>Ctrl+L</kbd>) apaga o conteúdo digitado, útil para iniciar uma nova seleção.</li>"
        "</ul></li>"
        "<li>Gerencie a lista visual de PDFs:<ul>"
        "<li>Arraste arquivos diretamente sobre a lista ou use o texto importado.</li>"
        "<li><b>🗑️ Remover</b> (<kbd>Del</kbd>) exclui o item destacado e <b>🧹 Limpar Lista</b> (<kbd>Ctrl+Shift+L</kbd>) limpa todos os itens.</li>"
        "<li>Reordene com <kbd>Ctrl+↑</kbd>/<kbd>Ctrl+↓</kbd> se necessário.</li>"
        "</ul></li>"
        "<li><b>🔍 Verificar</b> (<kbd>Ctrl+Shift+V</kbd>): confirma existência de cada arquivo, gerando relatório de inconsistências.</li>"
        "<li><b>🖨️ Imprimir</b> (<kbd>Ctrl+P</kbd>): inicia fila usando o mecanismo disponível (Foxit/Adobe/padrão) com barra de progresso.</li>"
        "</ol>"
        "<h4><b>Indicadores Visuais</b></h4><ul>"
        "<li>Linhas ausentes no disco listadas no relatório com mensagem descritiva.</li>"
        "<li>Progresso percentual exibido durante verificação e impressão.</li>"
        "</ul>",
    ),
    "comparar": (
        "<h2>Comparador de Arquivos</h2>",
        "<ol>"
        "<li>Selecione o tipo de arquivo; formatos com dependências ausentes aparecem desativados e exibem alerta inicial.</li>"
        "<li>Alimente as listas paralelas:<ul>"
        "<li>➕ <b>Adicionar à Lista A/B</b> abre seletor filtrado pelas extensões suportadas.</li>"
        "<li>Arraste arquivos sobre cada tabela; coluna <b>#</b> mantém ordem lógica.</li>"
        "<li>Duplicados/inexistentes são descartados com avisos.</li>"
        "</ul></li>"
        "<li>Organize pares equivalentes:<ul>"
        "<li>Alinhe nomes na coluna <b>Arquivo</b> para correspondência correta.</li>"
        "<li>Remova entradas com <kbd>Delete</kbd>.</li>"
        "</ul></li>"
        "<li>Execute 🔄 <b>Comparar</b>; progresso exibido na barra inferior e linhas recebem status.</li>"
        "<li>Avalie resultados:<ul>"
        "<li><b>Status</b>: ✓ sucesso • ✗ divergência — tooltip detalha a diferença.</li>"
        "<li>Tooltips de arquivos listam propriedades extraídas (hash, entidades CAD, volume, etc.).</li>"
        "</ul></li>"
        "<li>Use 🛑 <b>Cancelar</b> para abortar em andamento e 🧹 <b>Limpar</b> para reiniciar.</li>"
        "</ol>"
        "<h4><b>Indicadores Visuais</b></h4><ul>"
        "<li>✓ = equivalência dentro dos critérios; ✗ = divergência ou falha de leitura.</li>"
        "<li>Tooltip de linha explica o motivo da marca ✗ (diferença, ausência, erro).</li>"
        "</ul>"
        "<h4><b>Atalhos</b></h4><ul>"
        "<li><kbd>Ctrl+O</kbd> Adicionar arquivos à lista ativa (botão ➕).</li>"
        "<li><kbd>Ctrl+Enter</kbd> Executar comparação (🔄 Comparar).</li>"
        "<li><kbd>Esc</kbd> Cancelar processamento (🛑 Cancelar) quando ativo.</li>"
        "<li><kbd>Ctrl+L</kbd> Limpar listas e estado (🧹 Limpar).</li>"
        "<li><kbd>Delete</kbd> Remover itens selecionados em cada tabela.</li>"
        "</ul>",
    ),
    "converter": (
        "<h2>Conversor de Arquivos</h2>",
        "<ol>"
        "<li>Selecione o <b>Tipo de Conversão</b>; opções habilitadas dependem das bibliotecas detectadas (ODA, Pillow, ezdxf/matplotlib, Inkscape).</li>"
        "<li>Monte a lista de origem:<ul>"
        "<li>➕ <b>Adicionar Arquivos</b> abre diálogo filtrado pelo fluxo.</li>"
        "<li>Arraste arquivos sobre a tabela; coluna <b>#</b> mantém a ordem.</li>"
        "<li>Use <kbd>Delete</kbd> para remover seleção rapidamente.</li>"
        "<li>Primeiro item sugere pasta de destino automaticamente.</li>"
        "</ul></li>"
        "<li>Defina a pasta de saída via 📁 <b>Procurar</b> ou digitando o caminho.</li>"
        "<li>Dispare 🚀 <b>Converter</b>; barra inferior mostra progresso percentual.</li>"
        "<li>Aba <b>Resultado</b>: ✓/✗ + tooltip de mensagem; duplo clique abre arquivo convertido.</li>"
        "<li>Use 🛑 <b>Cancelar</b> para abortar e 🧹 <b>Limpar</b> para reiniciar listas e estado.</li>"
        "</ol>"
        "<h4><b>Indicadores Visuais</b></h4><ul>"
        "<li>✓ conversão concluída com sucesso; ✗ falha — tooltip descreve a causa.</li>"
        "<li>Progresso acumulado reflete itens processados / total.</li>"
        "</ul>"
        "<h4><b>Atalhos</b></h4><ul>"
        "<li><kbd>Ctrl+O</kbd> Adicionar arquivos de origem.</li>"
        "<li><kbd>Ctrl+Enter</kbd> Iniciar conversão (🚀 Converter).</li>"
        "<li><kbd>Esc</kbd> Cancelar conversão em andamento.</li>"
        "<li><kbd>Ctrl+L</kbd> Limpar tabelas e resetar formulário.</li>"
        "<li><kbd>Delete</kbd> Remover itens selecionados na tabela de origem.</li>"
        "</ul>",
    ),
    "cadastro": (
        "<h2>Formulários de Cadastro</h2>",
        "<ol>"
        "<li><b>Login necessário</b>: operações de inclusão, edição e exclusão exigem sessão ativa; sem login botões de ação permanecem desativados.</li>"
        "<li><b>Entenda a estrutura</b>: o painel superior concentra os filtros de busca, o centro reúne a lista paginada por tipo e a seção inferior exibe campos de inclusão/edição com os botões de ação correspondentes. Os títulos da janela e do quadro variam automaticamente entre <i>Adicionar</i> e <i>Editar/Excluir</i>, e os controles extras (✏️ Atualizar / 🗑️ Excluir) só surgem no modo edição.</li>"
        "<li><b>Localize registros rapidamente</b>: digite nos campos de busca ou ajuste as combos para filtrar em tempo real; a consulta é disparada automaticamente com debounce e preserva a ordenação. Use 🧹 <b>Limpar</b> (<kbd>Ctrl+R</kbd>) para zerar os filtros e recarregar a tabela.</li>"
        "<li><b>Inclua novos itens</b>: preencha os campos obrigatórios no quadro inferior e confirme com ➕ <b>Adicionar</b> (<kbd>Ctrl+Enter</kbd>). Em deduções, escolha primeiro Material/Espessura/Canal nas combos internas para relacionar o trio corretamente. O controlador valida duplicidades, converte números com vírgula/ponto e registra o log da operação; ao sucesso, os campos são limpos e as listas/combos de outros formulários são atualizadas via cache.</li>"
        "<li><b>Edite com segurança</b>: ao abrir pelo menu de edição, escolha uma linha na lista para que os campos sejam preenchidos automaticamente. Ajuste os valores desejados e confirme com ✏️ <b>Atualizar</b> (<kbd>Ctrl+S</kbd>); uma caixa de confirmação precede a gravação. Se nada mudar, o sistema informa que não houve alterações.</li>"
        "<li><b>Exclua registros</b>: selecione a linha e use 🗑️ <b>Excluir</b> (<kbd>Delete</kbd>). Materiais, espessuras e canais removem as deduções associadas em cascata, enquanto deduções isoladas afetam apenas o par escolhido. Todas as ações geram logs e invalidam o cache correspondente para refletir no restante da aplicação.</li>"
        "</ol>",
    ),
    "razao_rie": (
        "<h2>Raio Interno / Espessura</h2>",
        "<ol>"
        "<li>Painel superior:<ul>"
        "<li>O rótulo <b>Raio Int. / Esp.</b> exibe a razão calculada dinamicamente conforme os dados da tela principal.</li>"
        "<li>A borda em relevo facilita copiar o valor via clique direito padrão do sistema.</li>"
        "</ul></li>"
        "<li>Tabela de referência:<ul>"
        "<li>Colunas “Razão” e “Fator K” listam pares cadastrados no banco (<b>g.RAIO_K</b>).</li>"
        "<li>A seleção é por linha; use setas ou clique para comparar o fator aconselhado com o resultado atual.</li>"
        "<li>A tabela é somente leitura, aceita ordenação e alterna cores para rápida inspeção.</li>"
        "</ul></li>"
        "<li>Quadro de aviso:<ul>"
        "<li>Realça que os valores são teóricos e devem ser validados em bancada antes de ajustes definitivos.</li>"
        "<li>O texto está concentrado em vermelho e permanece fixo, sem necessidade de rolagem.</li>"
        "</ul></li>"
        "</ol>"
        "<h4><b>Atalhos</b></h4><p>Sem atalhos dedicados; interação apenas por seleção e rolagem padrão.</p>",
    ),
    "autenticacao": (
        "<h2>Autenticação de Usuários</h2>",
        "<ol>"
        "<li>Preencha os campos obrigatórios:<ul>"
        "<li><b>Usuário</b>: foco rápido com <kbd>Ctrl+U</kbd>.</li>"
        "<li><b>Senha</b>: foco rápido com <kbd>Ctrl+P</kbd>; o conteúdo fica oculto.</li>"
        "</ul></li>"
        "<li>Escolha o fluxo conforme o contexto:<ul>"
        "<li><b>Login</b>: pressione 🔐 <b>Login</b> ou <kbd>Enter</kbd> para autenticar-se. Erros exibem mensagens e limpam apenas a senha.</li>"
        "<li><b>Novo Usuário</b>: quando aberto pelo cadastro, o botão muda para 💾 <b>Salvar</b>. O sistema verifica na base se já existe administrador:<ul>"
        "<li>Se <b>não houver admin registrado</b>, o checkbox <b>Admin</b> (<kbd>Ctrl+A</kbd>) aparece destacado para que o primeiro usuário seja cadastrado com privilégios elevados.</li>"
        "<li>Se a consulta ao banco falhar, a janela alerta e restringe o cadastro ao perfil viewer para evitar múltiplos admins acidentalmente.</li>"
        "</ul></li>"
        "</ul></li>"
        "<li>Finalize ou cancele:<ul>"
        "<li>A tecla <kbd>Esc</kbd> fecha a janela a qualquer momento.</li>"
        "<li>Após login bem-sucedido, a janela é fechada e o formulário original prossegue com a sessão autenticada.</li>"
        "</ul></li>"
        "</ol>",
    ),
    "manual": (
        "<h2>Manual de Uso</h2>",
        "<ol>"
        "<li>Use o botão <b>☰ Categorias</b> para abrir o menu lateral; quando expandido, o texto muda para ✖ <b>Fechar categorias</b>."
        "</li>"
        "<li>Navegue pelas seções:<ul>"
        "<li>Cada item da lista seleciona a página correspondente no painel principal.</li>"
        "<li>Se o manual for aberto por outra janela, a categoria associada já chega destacada.</li>"
        "</ul></li>"
        "<li>Leia o conteúdo rico:<ul>"
        "<li>Os cartões exibem títulos destacados e texto formatado com listas, tabelas e links externos (em azul).</li>"
        "<li>A rolagem é independente por seção; use o mouse ou a barra de rolagem do cartão.</li>"
        "</ul></li>"
        "<li>Pressione o ícone de ajuda da barra superior para voltar rapidamente à seção “Manual de Uso”.</li>"
        "<li>Não há atalhos específicos adicionais além dos globais (ajuda, foco, rolagem).</li>"
        "</ol>",
    ),
    "sobre": (
        "<h2>Janela Sobre</h2>",
        "<ol>"
        "<li>O cabeçalho personalizado mostra o título e oferece atalho para esta ajuda.</li>"
        "<li>O corpo central exibe:<ul>"
        "<li><b>Nome do aplicativo</b> e <b>versão</b> atual (extraída de <code>__version__</code>).</li>"
        "<li><b>Autor</b> responsável pelo projeto.</li>"
        "<li>Descrição resumida da finalidade da ferramenta.</li>"
        "</ul></li>"
        "<li>O link “Repositório no GitHub” abre o navegador padrão para consulta de código-fonte e releases.</li>"
        "<li>Pressione <kbd>Esc</kbd> para fechar rapidamente.</li>"
        "</ol>",
    ),
    "admin": (
        "<h2>Ferramenta Administrativa</h2>",
        "<ol>"
        "<li>Autentique-se:<ul>"
        "<li>Informe usuário/senha e confirme em 🔐 <b>Acessar Ferramenta</b>. Atalhos: <kbd>Enter</kbd>, <kbd>Ctrl+U</kbd>, <kbd>Ctrl+P</kbd>.</li>"
        "<li>Após sucesso, a janela expande para exibir as abas principais.</li>"
        "</ul></li>"
        "<li>Aba 🔧 <b>Gerenciar Instâncias</b>:<ul>"
        "<li>Tabela “Lista de instâncias” mostra sessão, hostname e última atividade (ordenação e seleção por linha).</li>"
        "<li>Botões:<ul>"
        "<li>🔄 <b>Atualizar</b> (<kbd>F5</kbd>/<kbd>Ctrl+R</kbd>): recarrega as sessões ativas.</li>"
        "<li>⚠️ <b>Shutdown Geral</b> (<kbd>Ctrl+Shift+Q</kbd>): solicita confirmação e envia comando para fechar todas as instâncias, exibindo progresso no rodapé.</li>"
        "</ul></li>"
        "<li>O contador superior mostra total de instâncias e horário da última verificação; atualizações automáticas ocorrem a cada 10 s.</li>"
        "</ul></li>"
        "<li>Aba 👥 <b>Gerenciar Usuários</b>:<ul>"
        "<li>Filtro “Usuário” com busca incremental e atalhos <kbd>Ctrl+F</kbd> para focar e <kbd>Ctrl+L</kbd> para limpar.</li>"
        "<li>Tabela lista ID oculto, nome, permissão (viewer/editor/admin) e flag de senha resetada.</li>"
        "<li>Ações por linha:<ul>"
        "<li>👤 <b>Alterar Permissão</b> (<kbd>Ctrl+A</kbd>): alterna entre viewer e editor (admins não podem ser rebaixados nem excluídos).</li>"
        "<li>🔄 <b>Resetar Senha</b> (<kbd>Ctrl+R</kbd>): define senha temporária “nova_senha”.</li>"
        "<li>🗑️ <b>Excluir</b> (<kbd>Delete</kbd>): remove o usuário após confirmação.</li>"
        "</ul></li>"
        "</ul></li>"
        "<li>Aba 🔄 <b>Atualizador</b>:<ul>"
        "<li>Mostra versão instalada e permite escolher pacote .zip via <b>Selecionar...</b> (<kbd>Ctrl+O</kbd>).</li>"
        "<li>Após escolher o arquivo, habilita o botão <b>Instalar Atualização</b> (<kbd>Ctrl+I</kbd>), que fecha instâncias e acompanha o progresso em barra dedicada.</li>"
        "<li>Mensagens de status indicam etapas; ao concluir, a view retorna para a tela inicial e limpa o caminho.</li>"
        "</ul></li>"
        "<li>Use <kbd>Ctrl+1</kbd>, <kbd>Ctrl+2</kbd> e <kbd>Ctrl+3</kbd> para alternar rapidamente entre as abas.</li>"
        "</ol>"
        "<h4><b>Resumo de Atalhos</b></h4><ul>"
        "<li><kbd>Ctrl+1/2/3</kbd> Abas • <kbd>F5</kbd>/<kbd>Ctrl+R</kbd> Atualizar instâncias • <kbd>Ctrl+Shift+Q</kbd> Shutdown Geral • <kbd>Ctrl+A</kbd> Alterar permissão • <kbd>Ctrl+R</kbd> Resetar senha • <kbd>Delete</kbd> Excluir usuário.</li>"
        "</ul>",
    ),
}


def register_manual_launcher(launcher: ManualLauncher) -> None:
    """Registra o callback responsável por abrir o manual completo."""

    global _manual_launcher  # pylint: disable=global-statement
    _manual_launcher = launcher


def show_help(key: str, parent: QWidget | None = None) -> None:
    """Exibe o conteúdo de ajuda associado à chave fornecida."""

    try:
        if _manual_launcher is not None:
            _manual_launcher(parent, key, True)
            return
    except RuntimeError:  # pragma: no cover - fallback
        pass

    title, message = _HELP_CONTENT.get(key, _DEFAULT_ENTRY)
    show_info(title, message, parent=parent)


def get_help_entry(key: str) -> HelpEntry:
    """Retorna a entrada de ajuda correspondente à chave ou o fallback padrão."""
    return _HELP_CONTENT.get(key, _DEFAULT_ENTRY)


def iter_help_entries(
    keys: Iterable[str] | None = None,
    *,
    include_missing: bool = True,
) -> Iterator[Tuple[str, HelpEntry]]:
    """Itera sobre entradas de ajuda.

    Args:
        keys: ordem opcional de chaves desejadas.
        include_missing: se True, chaves desconhecidas rendem fallback padrão.
    """

    if keys is not None:
        seen: List[str] = []
        for key in keys:
            if key in seen:
                continue
            entry = _HELP_CONTENT.get(key)
            if entry is None:
                if include_missing:
                    seen.append(key)
                    yield key, _DEFAULT_ENTRY
                continue
            seen.append(key)
            yield key, entry

        for key, entry in _HELP_CONTENT.items():
            if key not in seen:
                yield key, entry
        return

    yield from _HELP_CONTENT.items()
