"""
Formulário Principal do Aplicativo de Calculadora de Dobra.
"""

import json
import logging
import os
import signal
import sys
import time
import traceback
from functools import partial

import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

from src import __version__
from src.components.barra_titulo import BarraTitulo
from src.components.menu_custom import MenuCustom
from src.config import globals as g
from src.forms import (
    form_aut,
    form_impressao,
    form_razao_rie,
    form_sobre,
)
from src.forms.form_universal import form_canal_main as FormCanal
from src.forms.form_universal import form_deducao_main as FormDeducao
from src.forms.form_universal import form_espessura_main as FormEspessura
from src.forms.form_universal import form_material_main as FormMaterial
from src.models.models import Usuario
from src.utils import ipc_manager
from src.utils.banco_dados import get_session, inicializar_banco_dados
from src.utils.estilo import (
    aplicar_tema_inicial,
    aplicar_tema_qdarktheme,
    obter_tema_atual,
    obter_temas_disponiveis,
    registrar_tema_actions,
)
from src.utils.interface_manager import carregar_interface
from src.utils.janelas import Janela
from src.utils.session_manager import (
    atualizar_heartbeat_sessao,
    limpar_sessoes_inativas,
    registrar_sessao,
    remover_sessao,
    verificar_comando_sistema,
)
from src.utils.update_manager import set_installed_version
from src.utils.usuarios import logout
from src.utils.utilitarios import (
    CONFIG_FILE,
    ICON_PATH,
    aplicar_medida_borda_espaco,
    setup_logging,
)

# Constantes para configuração da aplicação
APP_VERSION = __version__
JANELA_PRINCIPAL_LARGURA = 360
JANELA_PRINCIPAL_ALTURA = 513
TIMER_SISTEMA_INTERVALO = 10000  # 10s para verificação mais rápida de comandos
LAYOUT_ESPACAMENTO = 0
LAYOUT_MARGEM = 0
VALORES_W_INICIAL = [1]


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
                form_aut.main(g.PRINC_FORM)
            else:
                logging.info("Administrador encontrado.")
    except SQLAlchemyError as e:
        logging.critical("Não foi possível verificar administrador no DB: %s", e)
        fechar_aplicativo()


def carregar_configuracao():
    """Carrega a configuração do aplicativo."""
    logging.info("Carregando configurações de %s", CONFIG_FILE)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    logging.warning(
        "Arquivo de configuração não encontrado. Usando configuração padrão."
    )
    return {"tema": "dark", "geometry": None}


def salvar_configuracao(config):
    """Salva a configuração do aplicativo."""
    logging.info("Salvando configurações em %s", CONFIG_FILE)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def salvar_tema_atual(tema):
    """Salva o tema atual no arquivo de configuração."""
    try:
        config = carregar_configuracao()
        config["tema"] = tema
        salvar_configuracao(config)
        logging.info("Tema salvo: %s", tema)
    except (OSError, IOError, json.JSONDecodeError) as e:
        logging.error("Erro ao salvar tema: %s", e)


def salvar_estado_final():
    """Salva a geometria da janela e outras configurações antes de fechar."""
    logging.info("Salvando estado final do aplicativo.")
    try:
        if g.PRINC_FORM:
            pos = g.PRINC_FORM.pos()
            geometry_string = f"+{pos.x()}+{pos.y()}"
            config = carregar_configuracao()
            config["geometry"] = geometry_string
            tema_atual = obter_tema_atual()
            if tema_atual:
                config["tema"] = tema_atual
            salvar_configuracao(config)
            logging.info("Estado final salvo com geometria: %s", geometry_string)
    except (OSError, IOError, json.JSONDecodeError) as e:
        logging.error("Erro ao salvar o estado final: %s", e, exc_info=True)


def _aplicar_e_salvar_tema(tema):
    """Aplica um tema e salva automaticamente a escolha."""
    aplicar_tema_qdarktheme(tema)
    salvar_tema_atual(tema)


def fechar_aplicativo():
    """Fecha o aplicativo de forma segura."""
    logging.info("Iniciando o processo de fechamento do aplicativo.")
    try:
        if g.PRINC_FORM:
            salvar_estado_final()
            g.PRINC_FORM.close()
        app = QApplication.instance()
        if app:
            app.quit()
    except (RuntimeError, AttributeError) as e:
        logging.error("Erro durante o fechamento do aplicativo: %s", e)
        sys.exit(0)


def configurar_janela_principal(config):
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

    g.PRINC_FORM = QMainWindow()
    g.PRINC_FORM.setWindowTitle(f"Calculadora de Dobra - v{APP_VERSION}")
    g.PRINC_FORM.setFixedSize(JANELA_PRINCIPAL_LARGURA, JANELA_PRINCIPAL_ALTURA)
    g.PRINC_FORM.is_main_window = True
    g.PRINC_FORM.setWindowFlags(
        Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
    )

    if "geometry" in config and isinstance(config["geometry"], str):
        parts = config["geometry"].split("+")
        if len(parts) >= 3:
            try:
                x, y = int(parts[1]), int(parts[2])
                g.PRINC_FORM.move(x, y)
            except (ValueError, IndexError):
                logging.warning("Geometria salva inválida: %s", config["geometry"])

    if ICON_PATH and os.path.exists(ICON_PATH):
        g.PRINC_FORM.setWindowIcon(QIcon(ICON_PATH))
    else:
        logging.error("Arquivo de ícone não encontrado em: %s", ICON_PATH)

    g.PRINC_FORM.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, True)
    logging.info("Configuração da janela principal concluída.")


def abrir_formulario(form_function, edit_flag_name, is_edit_mode):
    """Abre um formulário genérico, configurando a flag de edição."""
    setattr(g, edit_flag_name, is_edit_mode)
    form_function(g.PRINC_FORM)


def _executar_autenticacao(is_login):
    """Abre o formulário de autenticação para login ou novo usuário."""
    setattr(g, "LOGIN", is_login)
    form_aut.main(g.PRINC_FORM)


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


def configurar_menu(menu_custom):
    """Configura o menu superior da janela principal."""
    if menu_custom is None:
        return
    menu_bar = menu_custom.get_menu_bar()

    estrutura_menu = {
        "📁 Arquivo": [
            (
                "➕ Nova Dedução",
                partial(abrir_formulario, FormDeducao, "EDIT_DED", False),
            ),
            (
                "➕ Novo Material",
                partial(abrir_formulario, FormMaterial, "EDIT_MAT", False),
            ),
            (
                "➕ Nova Espessura",
                partial(abrir_formulario, FormEspessura, "EDIT_ESP", False),
            ),
            (
                "➕ Novo Canal",
                partial(abrir_formulario, FormCanal, "EDIT_CANAL", False),
            ),
            ("separator", None),
            ("🚪 Sair", fechar_aplicativo),
        ],
        "✏️ Editar": [
            (
                "📝 Editar Dedução",
                partial(abrir_formulario, FormDeducao, "EDIT_DED", True),
            ),
            (
                "📝 Editar Material",
                partial(abrir_formulario, FormMaterial, "EDIT_MAT", True),
            ),
            (
                "📝 Editar Espessura",
                partial(abrir_formulario, FormEspessura, "EDIT_ESP", True),
            ),
            (
                "📝 Editar Canal",
                partial(abrir_formulario, FormCanal, "EDIT_CANAL", True),
            ),
        ],
        "🔧 Utilidades": [
            ("➗ Razão Raio/Espessura", lambda: form_razao_rie.main(g.PRINC_FORM)),
            ("🖨️ Impressão em Lote", lambda: form_impressao.main(g.PRINC_FORM)),
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
    opcoes_menu.addSeparator()

    temas_menu = opcoes_menu.addMenu("🎨 Temas")
    temas_actions = {}
    for tema in obter_temas_disponiveis():
        action = QAction(tema.capitalize(), g.PRINC_FORM, checkable=True)
        action.setChecked(tema == getattr(g, "TEMA_ATUAL", "dark"))
        action.triggered.connect(lambda checked, t=tema: _aplicar_e_salvar_tema(t))
        temas_menu.addAction(action)
        temas_actions[tema] = action
    registrar_tema_actions(temas_actions)


def _criar_menu_ajuda(menu_bar):
    """Cria o menu Ajuda."""
    help_menu = menu_bar.addMenu("❓ Ajuda")
    sobre_action = QAction(f"ℹ️ Sobre (v{APP_VERSION})", g.PRINC_FORM)
    sobre_action.triggered.connect(lambda: form_sobre.main(g.PRINC_FORM))
    help_menu.addAction(sobre_action)


def configurar_frames():
    """Configura os frames principais da janela."""
    logging.info("Configurando os frames da UI.")
    central_widget = QWidget()
    g.PRINC_FORM.setCentralWidget(central_widget)
    vlayout = QVBoxLayout(central_widget)
    aplicar_medida_borda_espaco(vlayout, LAYOUT_MARGEM, LAYOUT_ESPACAMENTO)

    tema_atual = getattr(g, "TEMA_ATUAL", "dark")
    g.BARRA_TITULO = BarraTitulo(g.PRINC_FORM, tema=tema_atual)
    vlayout.addWidget(g.BARRA_TITULO)

    if hasattr(g, "BARRA_TITULO") and g.BARRA_TITULO:
        g.BARRA_TITULO.set_tema(obter_tema_atual())

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
        fechar_aplicativo()
        return

    atualizar_heartbeat_sessao()


def iniciar_timers():
    """Inicializa e armazena os QTimers no objeto global 'g'."""
    TIMER_SISTEMA.timeout.connect(system_tick)
    TIMER_SISTEMA.start(TIMER_SISTEMA_INTERVALO)


def verificar_instancias_multiplas():
    """Verifica se há múltiplas instâncias rodando."""
    try:

        # Conta processos Python que podem estar acessando o banco
        processos_python = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                if proc.info["name"] and "python" in proc.info["name"].lower():
                    cmdline = proc.info["cmdline"]
                    if cmdline and any("tabela" in arg.lower() for arg in cmdline):
                        processos_python.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if len(processos_python) > 1:
            logging.warning(
                "Detectadas %d instâncias Python. Possível concorrência.",
                len(processos_python),
            )

            # Aguarda um pouco para outras instâncias terminarem
            time.sleep(2)
    except (ImportError, OSError, RuntimeError) as e:
        logging.warning("Erro ao verificar instâncias múltiplas: %s", e)


def main():
    """Função principal que inicializa e executa a aplicação."""
    setup_logging("app.log", log_to_console=True)
    app = None
    try:
        logging.info("Iniciando a aplicação v%s...", APP_VERSION)

        # Verifica instâncias múltiplas primeiro
        verificar_instancias_multiplas()

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
        config = carregar_configuracao()
        tema_salvo = config.get("tema", "dark")
        aplicar_tema_inicial(tema_salvo)

        app.aboutToQuit.connect(salvar_estado_final)
        app.aboutToQuit.connect(remover_sessao)

        configurar_janela_principal(config)
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
    except (OSError, IOError, json.JSONDecodeError, RuntimeError) as e:
        logging.critical("ERRO CRÍTICO na inicialização: %s", e, exc_info=True)

    if app:
        app.quit()
    return 1


if __name__ == "__main__":
    sys.exit(main())
