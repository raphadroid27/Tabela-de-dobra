# -*- coding: utf-8 -*-
"""
Formulário Principal do Aplicativo de Cálculo de Dobra.

Este módulo implementa a interface principal do aplicativo, permitindo a gestão
de deduções, materiais, espessuras e canais. Utiliza PySide6 para a interface
gráfica, além de módulos auxiliares para banco de dados, variáveis globais e
funcionalidades específicas, incluindo um sistema de atualização controlado.

Versão Refatorada: Reduz a redundância na criação de menus e na abertura de
formulários, centralizando a lógica e melhorando a manutenibilidade.
"""

import json
import logging
import os
import signal
import sys
import traceback
import uuid
from functools import partial

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QApplication, QGridLayout, QMainWindow,
                               QVBoxLayout, QWidget)
from sqlalchemy.exc import SQLAlchemyError

from src import __version__
from src.components.barra_titulo import BarraTitulo
from src.components.menu_custom import MenuCustom
from src.config import globals as g
from src.forms import (form_aut, form_impressao, form_razao_rie, form_sobre,
                       form_usuario)
from src.forms.form_wrappers import (FormCanal, FormDeducao, FormEspessura,
                                     FormMaterial)
from src.models.models import Usuario
from src.utils.banco_dados import inicializar_banco_dados
from src.utils.banco_dados import session as db_session
from src.utils.estilo import (aplicar_tema_inicial, aplicar_tema_qdarktheme,
                              obter_tema_atual, obter_temas_disponiveis,
                              registrar_tema_actions)
from src.utils.interface_manager import carregar_interface
from src.utils.janelas import (aplicar_no_topo_app_principal,
                               remover_janelas_orfas)
from src.utils.session_manager import (atualizar_heartbeat_sessao,
                                       obter_comando_sistema, registrar_sessao,
                                       remover_sessao)
# --- MODIFICAÇÃO: Importar as funções corretas ---
from src.utils.update_manager import (checagem_periodica_update,
                                      manipular_clique_update,
                                      set_installed_version)
from src.utils.usuarios import logout
from src.utils.utilitarios import (CONFIG_FILE, ICON_PATH,
                                   aplicar_medida_borda_espaco,
                                   setup_logging)

# --- Variáveis Globais de Configuração e Versão ---
APP_VERSION = __version__
g.SESSION_ID = str(uuid.uuid4())


# --- Funções de Gerenciamento da Aplicação ---
def verificar_admin_existente():
    """Verifica se existe um administrador cadastrado."""
    logging.info("Verificando se existe um administrador.")
    admin_existente = db_session.query(Usuario).filter(
        Usuario.role == "admin").first()
    if not admin_existente:
        logging.warning(
            "Nenhum administrador encontrado. Abrindo formulário de autorização.")
        form_aut.main(g.PRINC_FORM)
    else:
        logging.info("Administrador encontrado.")


def carregar_configuracao():
    """Carrega a configuração do aplicativo."""
    logging.info("Carregando configurações de %s", CONFIG_FILE)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    logging.warning(
        "Arquivo de configuração não encontrado. Usando configuração padrão.")
    return {}


def salvar_configuracao(config):
    """Salva a configuração do aplicativo."""
    logging.info("Salvando configurações em %s", CONFIG_FILE)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)


def fechar_aplicativo():
    """Fecha o aplicativo de forma segura. A remoção da sessão é tratada por 'aboutToQuit'."""
    logging.info("Iniciando o processo de fechamento do aplicativo.")

    try:
        if g.PRINC_FORM:
            # Salva a geometria antes de fechar
            pos = g.PRINC_FORM.pos()
            config = carregar_configuracao()
            config['geometry'] = f"+{pos.x()}+{pos.y()}"
            salvar_configuracao(config)
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
    remover_janelas_orfas()
    if g.PRINC_FORM:
        try:
            g.PRINC_FORM.close()
            g.PRINC_FORM.deleteLater()
            g.PRINC_FORM = None
        except (RuntimeError, AttributeError):
            pass

    g.PRINC_FORM = QMainWindow()
    g.PRINC_FORM.setWindowTitle(f"Cálculo de Dobra - v{APP_VERSION}")
    g.PRINC_FORM.setFixedSize(360, 500)
    g.PRINC_FORM.is_main_window = True
    g.PRINC_FORM.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

    if 'geometry' in config and isinstance(config['geometry'], str):
        parts = config['geometry'].split('+')
        if len(parts) >= 3:
            try:
                x, y = int(parts[1]), int(parts[2])
                g.PRINC_FORM.move(x, y)
                logging.info(
                    "Janela movida para a posição salva: %d, %d", x, y)
            except (ValueError, IndexError):
                logging.warning("Geometria salva inválida: %s",
                                config['geometry'])

    icone_path = ICON_PATH
    if icone_path and os.path.exists(icone_path):
        g.PRINC_FORM.setWindowIcon(QIcon(icone_path))
    else:
        logging.error("Arquivo de ícone não encontrado em: %s", icone_path)

    g.PRINC_FORM.setAttribute(Qt.WA_QuitOnClose, True)
    logging.info("Configuração da janela principal concluída.")


# --- REATORAÇÃO: Lógica de Abertura de Formulários ---
def abrir_formulario(form_class, edit_flag_name, is_edit_mode):
    """
    Abre um formulário genérico, configurando a flag de edição correspondente.
    """
    setattr(g, edit_flag_name, is_edit_mode)
    form_class.main(g.PRINC_FORM)


def _executar_autenticacao(is_login):
    """Abre o formulário de autenticação para login ou novo usuário."""
    setattr(g, "LOGIN", is_login)
    form_aut.main(g.PRINC_FORM)


def _toggle_no_topo():
    """Alterna o estado 'sempre no topo' da janela principal."""
    aplicar_no_topo_app_principal()


# --- REATORAÇÃO: Configuração de Menus e Interface ---
def configurar_menu():
    """Configura o menu superior da janela principal de forma centralizada."""
    if not hasattr(g, 'MENU_CUSTOM') or g.MENU_CUSTOM is None:
        return
    menu_bar = g.MENU_CUSTOM.get_menu_bar()

    # Estrutura de dados que define todos os menus e suas ações
    estrutura_menu = {
        "📁 Arquivo": [
            ("➕ Nova Dedução", partial(abrir_formulario, FormDeducao, 'EDIT_DED', False)),
            ("➕ Novo Material", partial(
                abrir_formulario, FormMaterial, 'EDIT_MAT', False)),
            ("➕ Nova Espessura", partial(
                abrir_formulario, FormEspessura, 'EDIT_ESP', False)),
            ("➕ Novo Canal", partial(abrir_formulario, FormCanal, 'EDIT_CANAL', False)),
            ("separator", None),
            ("🚪 Sair", fechar_aplicativo)
        ],
        "✏️ Editar": [
            ("📝 Editar Dedução", partial(
                abrir_formulario, FormDeducao, 'EDIT_DED', True)),
            ("📝 Editar Material", partial(
                abrir_formulario, FormMaterial, 'EDIT_MAT', True)),
            ("📝 Editar Espessura", partial(
                abrir_formulario, FormEspessura, 'EDIT_ESP', True)),
            ("📝 Editar Canal", partial(abrir_formulario, FormCanal, 'EDIT_CANAL', True))
        ],
        "🔧 Utilidades": [
            ("➗ Razão Raio/Espessura", lambda: form_razao_rie.main(g.PRINC_FORM)),
            ("🖨️ Impressão em Lote", lambda: form_impressao.main(g.PRINC_FORM))
        ],
        "👤 Usuário": [
            ("🔐 Login", partial(_executar_autenticacao, True)),
            ("👥 Novo Usuário", partial(_executar_autenticacao, False)),
            ("⚙️ Gerenciar Usuários", lambda: form_usuario.main(g.PRINC_FORM)),
            ("separator", None),
            ("🚪 Sair", logout)
        ]
    }

    for nome_menu, acoes in estrutura_menu.items():
        menu = menu_bar.addMenu(nome_menu)
        _adicionar_acoes_ao_menu(menu, acoes)

    # Menus com lógica especial são criados separadamente
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
    """Cria o menu Opções (mantido separado por sua lógica complexa)."""
    opcoes_menu = menu_bar.addMenu("⚙️ Opções")
    if not hasattr(g, 'NO_TOPO_VAR') or g.NO_TOPO_VAR is None:
        g.NO_TOPO_VAR = False
    no_topo_action = QAction("📌 No topo", g.PRINC_FORM)
    no_topo_action.setCheckable(True)
    no_topo_action.setChecked(g.NO_TOPO_VAR)
    no_topo_action.triggered.connect(_toggle_no_topo)
    opcoes_menu.addAction(no_topo_action)

    temas_menu = opcoes_menu.addMenu("🎨 Temas")
    temas_actions = {}
    for tema in obter_temas_disponiveis():
        action = QAction(tema.capitalize(), g.PRINC_FORM)
        action.setCheckable(True)
        action.setChecked(tema == getattr(g, 'TEMA_ATUAL', 'dark'))
        action.triggered.connect(
            lambda checked, t=tema: aplicar_tema_qdarktheme(t))
        temas_menu.addAction(action)
        temas_actions[tema] = action
    registrar_tema_actions(temas_actions)


def _criar_menu_ajuda(menu_bar):
    """Cria o menu Ajuda (mantido separado por sua lógica de atualização)."""
    help_menu = menu_bar.addMenu("❓ Ajuda")
    sobre_action = QAction(f"ℹ️ Sobre (v{APP_VERSION})", g.PRINC_FORM)
    sobre_action.triggered.connect(lambda: form_sobre.main(g.PRINC_FORM))
    help_menu.addAction(sobre_action)
    help_menu.addSeparator()
    g.UPDATE_ACTION = QAction("🔄 Verificar Atualizações", g.PRINC_FORM)
    g.UPDATE_ACTION.triggered.connect(manipular_clique_update)
    help_menu.addAction(g.UPDATE_ACTION)


def configurar_frames():
    """Configura os frames principais da janela."""
    logging.info("Configurando os frames da UI.")
    central_widget = QWidget()
    g.PRINC_FORM.setCentralWidget(central_widget)
    vlayout = QVBoxLayout(central_widget)
    aplicar_medida_borda_espaco(vlayout, 0, 0)

    tema_atual = getattr(g, 'TEMA_ATUAL', 'dark')
    g.BARRA_TITULO = BarraTitulo(g.PRINC_FORM, tema=tema_atual)
    vlayout.addWidget(g.BARRA_TITULO)

    if hasattr(g, 'BARRA_TITULO') and g.BARRA_TITULO:
        g.BARRA_TITULO.set_tema(obter_tema_atual())

    g.MENU_CUSTOM = MenuCustom(g.PRINC_FORM)
    vlayout.addWidget(g.MENU_CUSTOM)

    conteudo_widget = QWidget()
    layout = QGridLayout(conteudo_widget)
    vlayout.addWidget(conteudo_widget)

    g.VALORES_W = [1]
    g.EXP_V = False
    g.EXP_H = False
    g.MAIN_LAYOUT = layout
    g.CARREGAR_INTERFACE_FUNC = carregar_interface
    carregar_interface(1, layout)
    logging.info("Configuração dos frames concluída.")


# --- Funções de Inicialização (Refatorado de main) ---
def configurar_sinais_excecoes():
    """Configura handlers para exceções não tratadas e sinais do sistema."""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if exc_type != KeyboardInterrupt:
            error_msg = "".join(traceback.format_exception(
                exc_type, exc_value, exc_traceback))
            logging.critical("ERRO NÃO TRATADO:\n%s", error_msg)

    def signal_handler(signum, _):
        logging.warning("Sinal %s recebido. Fechando o aplicativo.", signum)
        fechar_aplicativo()

    sys.excepthook = handle_exception
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def processar_verificacao_sistema():
    """Função chamada pelo timer para verificar o estado do sistema."""
    # 1. Avisa que a instância está viva
    atualizar_heartbeat_sessao()

    # 2. Verifica se há um comando para executar
    comando = obter_comando_sistema()

    # 3. Age com base no comando
    if comando == 'SHUTDOWN':
        fechar_aplicativo()


# --- FUNÇÃO MODIFICADA ---
def iniciar_timers():
    """Inicializa e armazena os QTimers no objeto global 'g' para mantê-los ativos."""
    g.TIMER_SISTEMA = QTimer()
    g.TIMER_SISTEMA.timeout.connect(processar_verificacao_sistema)
    g.TIMER_SISTEMA.start(5000)

    g.UPDATE_CHECK_TIMER = QTimer()
    # A função não precisa mais do argumento da versão, pois lê do DB
    g.UPDATE_CHECK_TIMER.timeout.connect(checagem_periodica_update)
    g.UPDATE_CHECK_TIMER.start(300000)  # 5 minutos
    # A verificação inicial também não precisa do argumento
    QTimer.singleShot(10000, checagem_periodica_update)  # 10 segundos


# --- Função Principal ---
def main():
    """Função principal que inicializa e executa a aplicação."""
    setup_logging('app.log', log_to_console=True)
    app = None
    try:
        logging.info("Iniciando a aplicação v%s...", APP_VERSION)
        inicializar_banco_dados()

        # --- NOVA LINHA ---
        # Garante que a versão no DB está correta na inicialização.
        # Esta é a "fonte da verdade" para a versão instalada.
        set_installed_version(APP_VERSION)
        # --- FIM DA NOVA LINHA ---

        configurar_sinais_excecoes()

        app = QApplication(sys.argv)
        aplicar_tema_inicial("dark")

        app.aboutToQuit.connect(remover_sessao)

        config = carregar_configuracao()
        configurar_janela_principal(config)
        configurar_frames()
        configurar_menu()

        registrar_sessao()
        verificar_admin_existente()

        if g.PRINC_FORM:
            g.PRINC_FORM.show()
            iniciar_timers()
            logging.info("Aplicativo iniciado. Entrando no loop de eventos.")
            return app.exec()

        logging.critical("ERRO FATAL: A janela principal não foi criada!")
        return 1

    except (RuntimeError, SQLAlchemyError, ImportError, FileNotFoundError, OSError) as e:
        logging.critical("ERRO CRÍTICO na inicialização: %s", e, exc_info=True)
        if app:
            app.quit()
        return 1
    finally:
        logging.info("Aplicação finalizada.")
        if db_session:
            db_session.close()


if __name__ == "__main__":
    sys.exit(main())
