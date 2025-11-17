"""Formulário principal do aplicativo de Calculadora de Dobra."""

import logging
import os
import signal
import sys
import traceback
from functools import partial

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from src import __version__
from src.components.menu_custom import MenuCustom
from src.config import globals as g
from src.forms import (
    form_aut,
    form_comparar_arquivos,
    form_converter_arquivos,
    form_impressao,
    form_manual,
    form_razao_rie,
    form_sobre,
)
from src.forms.form_universal import main as form_universal
from src.models.models import Usuario
from src.utils import ipc_manager
from src.utils.banco_dados import get_session, inicializar_banco_dados
from src.utils.theme_manager import theme_manager
from src.utils.interface_manager import carregar_interface
from src.utils.janelas import Janela
from src.utils.session_manager import (
    atualizar_heartbeat_sessao,
    limpar_sessoes_inativas,
    registrar_sessao,
    remover_sessao,
    verificar_comando_sistema,
)
# theme_manager is used for applying palettes and styles
from src.utils.update_manager import set_installed_version
from src.utils.usuarios import logout
from src.utils.utilitarios import (
    ICON_PATH,
    aplicar_medida_borda_espaco,
    setup_logging,
    show_timed_message_box,
)

# Constantes para configuração da aplicação
APP_VERSION = __version__
JANELA_PRINCIPAL_LARGURA = 360
JANELA_PRINCIPAL_ALTURA = 500
TIMER_SISTEMA_INTERVALO = 10000  # 10s para verificação mais rápida de comandos
LAYOUT_ESPACAMENTO = 0
LAYOUT_MARGEM = 0
VALORES_W_INICIAL = [1]


class MainWindow(QMainWindow):
    """Janela principal da aplicação com tratamento personalizado de fechamento."""

    def __init__(self):
        super().__init__()
        self.is_main_window = True
        # Inicializa a lista de callbacks de resize
        self._resize_handlers = []

    def closeEvent(self, event):  # pylint: disable=invalid-name
        """Evento chamado quando a janela principal está sendo fechada."""
        logging.info("CloseEvent da janela principal chamado.")
        Janela.fechar_janelas_dependentes()
        salvar_estado_final()
        event.accept()

    # Pequeno hook para permitir callbacks quando a janela for redimensionada
    def add_resize_handler(self, callback):
        """Registra um callback a ser chamado em eventos de resize.

        O callback receberá o evento de resize como único argumento.
        Use para atualizar dinamicamente elementos que dependem da largura/altura
        da janela (por exemplo: rótulos de menu compactos).
        """
        self._resize_handlers.append(callback)

    def resizeEvent(self, event):  # pylint: disable=invalid-name
        """Dispara os callbacks registrados quando a janela é redimensionada.

        A implementação chama os callbacks de forma segura, ignorando
        exceções para não interromper o fluxo da UI.
        """
        super().resizeEvent(event)
        for cb in list(self._resize_handlers):
            try:
                cb(event)
            except Exception:  # pylint: disable=broad-except
                # Não propagar exceções de callbacks de UI
                pass


TIMER_SISTEMA = QTimer()


def verificar_admin_existente():
    """Verifica se existe um administrador cadastrado."""
    logging.info("Verificando se existe um administrador.")
    try:
        with get_session() as session:
            admin_existente = (
                session.query(Usuario).filter(Usuario.role == "admin").first()
            )
            if not admin_existente:
                logging.warning(
                    "Nenhum administrador encontrado. Abrindo formulário de autorização."
                )
                form_aut.main(None)
            else:
                logging.info("Administrador encontrado.")
    except SQLAlchemyError as e:
        logging.critical("Não foi possível verificar administrador no DB: %s", e)
        fechar_aplicativo()


def salvar_estado_final():
    """Salva a geometria da janela usando QSettings."""
    logging.info("Salvando estado final do aplicativo.")
    try:
        if g.PRINC_FORM:
            settings = QSettings()
            pos = g.PRINC_FORM.pos()
            settings.setValue("app/pos_x", pos.x())
            settings.setValue("app/pos_y", pos.y())
            settings.sync()  # Força a sincronização
            logging.info("Estado final salvo com posição: x=%d, y=%d", pos.x(), pos.y())
    except (OSError, IOError, RuntimeError) as e:
        logging.error("Erro ao salvar o estado final: %s", e, exc_info=True)


def fechar_aplicativo():
    """Fecha o aplicativo de forma segura."""
    logging.info("Iniciando o processo de fechamento do aplicativo.")
    try:
        Janela.fechar_janelas_dependentes()
        if g.PRINC_FORM:
            salvar_estado_final()
            g.PRINC_FORM.close()
        app = QApplication.instance()
        if app:
            app.quit()
    except (RuntimeError, AttributeError) as e:
        logging.error("Erro durante o fechamento do aplicativo: %s", e)
        sys.exit(0)


def configurar_janela_principal():
    """Configura a janela principal do aplicativo."""
    logging.info("Configurando a janela principal.")
    Janela.remover_janelas_orfas()
    if g.PRINC_FORM:
        try:
            g.PRINC_FORM.close()
            g.PRINC_FORM.deleteLater()
            g.PRINC_FORM = None
        except (RuntimeError, AttributeError):
            pass

    g.PRINC_FORM = MainWindow()
    g.PRINC_FORM.setWindowTitle("Calculadora de Dobra")
    g.PRINC_FORM.setFixedSize(JANELA_PRINCIPAL_LARGURA, JANELA_PRINCIPAL_ALTURA)
    g.PRINC_FORM.setWindowFlags(Qt.WindowType.Window)

    # Carrega a posição da janela usando QSettings
    settings = QSettings()
    x = settings.value("app/pos_x", type=int)
    y = settings.value("app/pos_y", type=int)
    if x is not None and y is not None:
        g.PRINC_FORM.move(x, y)
    else:
        logging.warning("Posição da janela não encontrada em QSettings. Usando padrão.")

    if ICON_PATH and os.path.exists(ICON_PATH):
        g.PRINC_FORM.setWindowIcon(QIcon(ICON_PATH))
    else:
        logging.error("Arquivo de ícone não encontrado em: %s", ICON_PATH)

    g.PRINC_FORM.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, True)
    logging.info("Configuração da janela principal concluída.")


def abrir_formulario(form_type, edit_flag_name, is_edit_mode):
    """Abre um formulário genérico, configurando a flag de edição."""
    setattr(g, edit_flag_name, is_edit_mode)
    form_universal(form_type, None)


def _executar_autenticacao(is_login):
    """Abre o formulário de autenticação para login ou novo usuário."""
    setattr(g, "LOGIN", is_login)
    form_aut.main(None)


def _on_toggle_no_topo(checked: bool, transparencia_action: QAction):
    """Define o estado 'sempre no topo'."""
    Janela.set_on_top_state(checked)
    transparencia_action.setVisible(checked)
    if not checked and transparencia_action.isChecked():
        transparencia_action.setChecked(False)
        _on_toggle_transparencia(False)


def _on_toggle_transparencia(checked: bool):
    """Define o estado de 'transparência'."""
    Janela.set_transparency_state(checked)


def _on_tema_selecionado(tema: str, checked: bool):
    """Aplica o tema selecionado."""
    if checked:
        # Aplica o tema via ThemeManager (paleta + estilos globais)
        try:
            theme_manager.apply_theme(tema)
            logging.info("Tema '%s' aplicado.", tema)
        except (AttributeError, RuntimeError, TypeError) as e:
            # Registrar erros específicos — evita capturar exceções muito genéricas
            logging.error("Falha ao aplicar tema '%s': %s", tema, e, exc_info=True)


def configurar_menu(menu_custom):
    """Configura o menu superior da janela principal."""
    if menu_custom is None:
        return
    menu_bar = menu_custom.get_menu_bar()

    estrutura_menu = {
        "📄 Adicionar": [
            (
                "➕ Adicionar Dedução",
                partial(abrir_formulario, "deducao", "EDIT_DED", False),
            ),
            (
                "➕ Adicionar Material",
                partial(abrir_formulario, "material", "EDIT_MAT", False),
            ),
            (
                "➕ Adicionar Espessura",
                partial(abrir_formulario, "espessura", "EDIT_ESP", False),
            ),
            (
                "➕ Adicionar Canal",
                partial(abrir_formulario, "canal", "EDIT_CANAL", False),
            ),
        ],
        "✏️ Editar": [
            (
                "📝 Editar Dedução",
                partial(abrir_formulario, "deducao", "EDIT_DED", True),
            ),
            (
                "📝 Editar Material",
                partial(abrir_formulario, "material", "EDIT_MAT", True),
            ),
            (
                "📝 Editar Espessura",
                partial(abrir_formulario, "espessura", "EDIT_ESP", True),
            ),
            (
                "📝 Editar Canal",
                partial(abrir_formulario, "canal", "EDIT_CANAL", True),
            ),
        ],
        "🔧 Recursos": [
            ("➗ Razão Raio/Espessura", lambda: form_razao_rie.main(None)),
            ("🖨️ Impressão em Lote", lambda: form_impressao.main(None)),
            ("📊 Comparar Arquivos", lambda: form_comparar_arquivos.main(None)),
            (
                "🔄 Converter Arquivos",
                lambda: form_converter_arquivos.main(None),
            ),
        ],
        "👤 Usuário": [
            ("🔐 Login", partial(_executar_autenticacao, True)),
            ("👥 Novo Usuário", partial(_executar_autenticacao, False)),
            ("separator", None),
            ("🚪 Sair", logout),
        ],
    }

    for nome_menu, acoes in estrutura_menu.items():
        menu = menu_bar.addMenu(nome_menu)
        _adicionar_acoes_ao_menu(menu, acoes)

    _criar_menu_opcoes(menu_bar)
    _criar_menu_ajuda(menu_bar)


def _adicionar_acoes_ao_menu(menu, acoes):
    """Adiciona uma lista de ações a um menu."""
    for nome, funcao in acoes:
        if nome == "separator":
            menu.addSeparator()
        else:
            action = QAction(nome, g.PRINC_FORM)
            action.triggered.connect(funcao)
            menu.addAction(action)


def _criar_menu_opcoes(menu_bar):
    """Cria o menu Opções."""
    opcoes_menu = menu_bar.addMenu("⚙️ Opções")
    transparencia_action = QAction("👻 Transparência", g.PRINC_FORM, checkable=True)
    transparencia_action.setChecked(Janela.get_transparency_state())
    transparencia_action.triggered.connect(_on_toggle_transparencia)

    no_topo_action = QAction("📌 No topo", g.PRINC_FORM, checkable=True)
    no_topo_action.setChecked(Janela.get_on_top_state())
    no_topo_action.triggered.connect(
        lambda checked: _on_toggle_no_topo(checked, transparencia_action)
    )
    opcoes_menu.addAction(no_topo_action)
    opcoes_menu.addAction(transparencia_action)
    transparencia_action.setVisible(no_topo_action.isChecked())

    # Submenu de temas
    tema_menu = opcoes_menu.addMenu("🎨 Tema")
    tema_actions = {}
    # Mapeamento para rótulos do menu em Português
    tema_rotulos = {"light": "Claro", "dark": "Escuro"}

    for tema in theme_manager.available_themes():
        # Usa rótulo localizado quando disponível
        label = tema_rotulos.get(tema, tema.capitalize())
        action = QAction(label, g.PRINC_FORM, checkable=True)
        action.setChecked(tema == theme_manager.current_mode)
        action.triggered.connect(
            lambda checked, t=tema: _on_tema_selecionado(t, checked)
        )
        tema_menu.addAction(action)
        tema_actions[tema] = action

    # Registrar actions no theme_manager para sincronização automática
    try:
        theme_manager.register_actions(tema_actions)
    except AttributeError:
        # Fallback silêncioso caso o theme_manager não suporte registro
        pass

    # Submenu de cor de destaque dentro do menu Tema
    cor_menu = tema_menu.addMenu("🌈 Cor de destaque")
    cor_actions = {}
    try:
        for cor_key, (rotulo, cor_hex) in theme_manager.color_options().items():
            # Criar um ícone swatch pequeno com a cor de destaque
            try:
                pix = QPixmap(14, 14)
                pix.fill(QColor(cor_hex))
                p = QPainter(pix)
                # Desenhar borda sutil para legibilidade
                p.setPen(QColor(0, 0, 0, 120))
                p.drawRect(0, 0, pix.width() - 1, pix.height() - 1)
                p.end()
                icon = QIcon(pix)
            except (TypeError, ValueError, RuntimeError):
                # Caso algo falhe, usar um ícone em branco
                icon = QIcon()
            action = QAction(rotulo, g.PRINC_FORM, checkable=True)
            action.setIcon(icon)
            action.setChecked(cor_key == theme_manager.current_color)
            # Connect only when checked to avoid redundant calls
            action.triggered.connect(
                lambda checked, c=cor_key: theme_manager.apply_color(c) if checked else None)
            cor_menu.addAction(action)
            cor_actions[cor_key] = action
        # Registrar actions ao theme_manager para que fiquem sincronizadas
        theme_manager.register_color_actions(cor_actions)
    except AttributeError:
        # Fallback: silencioso caso não seja possível aplicar cores
        pass

    # Registrar menus para modo compacto via utilitário Janela
    try:
        Janela.register_compact_menu(opcoes_menu, threshold=g.MENU_COMPACT_WIDTH)
    except AttributeError:
        # Se por algum motivo a função não estiver disponível, seguir com o fluxo
        pass


def _criar_menu_ajuda(menu_bar):
    """Cria o menu Ajuda."""
    help_menu = menu_bar.addMenu("❓ Ajuda")
    manual_action = QAction("📘 Manual de Uso", g.PRINC_FORM)
    manual_action.triggered.connect(lambda: form_manual.main(None))
    help_menu.addAction(manual_action)
    sobre_action = QAction(f"ℹ️ Sobre (v{APP_VERSION})", g.PRINC_FORM)
    sobre_action.triggered.connect(lambda: form_sobre.main(None))
    help_menu.addAction(sobre_action)

    # Registrar menus para modo compacto via utilitário Janela (inclui ajuda)
    try:
        Janela.register_compact_menu(
            opcoes_menu=None, help_menu=help_menu, threshold=g.MENU_COMPACT_WIDTH)
    except AttributeError:
        # fallback
        pass


def configurar_frames():
    """Configura os frames principais da janela."""
    logging.info("Configurando os frames da UI.")
    central_widget = QWidget()
    g.PRINC_FORM.setCentralWidget(central_widget)
    vlayout = QVBoxLayout(central_widget)
    aplicar_medida_borda_espaco(vlayout, LAYOUT_MARGEM, LAYOUT_ESPACAMENTO)

    menu_custom = MenuCustom(g.PRINC_FORM)
    vlayout.addWidget(menu_custom)

    conteudo_widget = QWidget()
    layout = QGridLayout(conteudo_widget)
    vlayout.addWidget(conteudo_widget)

    g.VALORES_W = VALORES_W_INICIAL
    g.EXP_V = False
    g.EXP_H = False
    g.MAIN_LAYOUT = layout
    g.CARREGAR_INTERFACE_FUNC = carregar_interface
    carregar_interface(1, layout)
    logging.info("Configuração dos frames concluída.")
    return menu_custom


def configurar_sinais_excecoes():
    """Configura handlers para exceções não tratadas e sinais do sistema."""

    def handle_exception(exc_type, exc_value, exc_traceback):
        if exc_type is not KeyboardInterrupt:
            error_msg = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
            logging.critical("ERRO NÃO TRATADO:\n%s", error_msg)

    def signal_handler(signum, _):
        logging.warning("Sinal %s recebido. Fechando o aplicativo.", signum)
        fechar_aplicativo()

    sys.excepthook = handle_exception
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def system_tick():
    """
    Função chamada periodicamente pelo timer do sistema.

    Executa tarefas de manutenção como verificar comandos e atualizar heartbeat.
    """
    if verificar_comando_sistema():
        logging.info("Comando de encerramento recebido. Fechando a aplicação.")
        show_timed_message_box(
            g.PRINC_FORM,
            "Sistema",
            "O administrador solicitou o fechamento do sistema.\n"
            "A aplicação será encerrada.",
            10000,
        )
        # Agendar o fechamento da aplicação após a mensagem ser exibida
        QTimer.singleShot(500, QApplication.quit)
        return

    atualizar_heartbeat_sessao()


def iniciar_timers():
    """Inicializa e armazena os QTimers no objeto global 'g'."""
    TIMER_SISTEMA.timeout.connect(system_tick)
    TIMER_SISTEMA.start(TIMER_SISTEMA_INTERVALO)


def main():
    """Função principal que inicializa e executa a aplicação."""
    setup_logging("app.log", log_to_console=True)
    app = None
    try:
        logging.info("Iniciando a aplicação v%s...", APP_VERSION)

        ipc_manager.ensure_ipc_dirs_exist()
        inicializar_banco_dados()

        # Inicializa o cache de dados essenciais
        try:
            from src.utils.cache_manager import (  # pylint: disable=import-outside-toplevel
                cache_manager,
            )

            cache_manager.preload_cache()
            logging.info("Cache de dados inicializado com sucesso")
        except (OSError, RuntimeError, ImportError) as e:
            logging.warning("Erro ao inicializar cache: %s", e)

        limpar_sessoes_inativas()
        ipc_manager.clear_all_commands()

        set_installed_version(APP_VERSION)
        configurar_sinais_excecoes()
        app = QApplication(sys.argv)
        app.setOrganizationName("raphadroid27")
        app.setApplicationName("Tabela-de-dobra")
        theme_manager.initialize()  # Inicializa o tema salvo

        app.aboutToQuit.connect(salvar_estado_final)
        app.aboutToQuit.connect(remover_sessao)

        configurar_janela_principal()
        menu_custom = configurar_frames()
        configurar_menu(menu_custom)
        registrar_sessao()
        verificar_admin_existente()

        # Atualiza combos com dados do cache após carregar interface
        try:
            from src.utils.interface import (  # pylint: disable=import-outside-toplevel
                todas_funcoes,
            )

            todas_funcoes()
            logging.info("Combos inicializados com dados do cache")
        except (OSError, RuntimeError, ImportError) as e:
            logging.warning("Erro ao inicializar combos: %s", e)

        if g.PRINC_FORM:
            g.PRINC_FORM.show()
            iniciar_timers()
            logging.info("Aplicativo iniciado. Entrando no loop de eventos.")
            return app.exec()

        logging.critical("ERRO FATAL: A janela principal não foi criada!")
        return 1
    except SQLAlchemyError as e:
        logging.critical("ERRO CRÍTICO na inicialização (DB): %s", e, exc_info=True)
    except (OSError, IOError, RuntimeError) as e:
        logging.critical("ERRO CRÍTICO na inicialização: %s", e, exc_info=True)

    if app:
        app.quit()
    return 1


if __name__ == "__main__":
    sys.exit(main())
