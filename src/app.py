"""
Formulário Principal do Aplicativo de Cálculo de Dobra.

Este módulo implementa a interface principal do aplicativo, permitindo a gestão
de deduções, materiais, espessuras e canais. Utiliza PySide6 para a interface
gráfica, além de módulos auxiliares para banco de dados, variáveis globais e
funcionalidades específicas.
"""

import json
import os
import sys
import traceback
import signal
import uuid
import socket
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction

from src.utils.utilitarios import obter_caminho_icone
from src.utils.usuarios import logout
from src.utils.janelas import (
    aplicar_no_topo_app_principal, remover_janelas_orfas)
from src.utils.interface_manager import carregar_interface
from src.utils.utilitarios import aplicar_medida_borda_espaco
from src.utils.banco_dados import session as db_session
from src.models.models import Usuario, SystemControl
from src.forms import (
    form_sobre,
    form_aut,
    form_usuario,
    form_razao_rie,
    form_impressao
)
from src.forms.form_wrappers import (
    FormEspessura,
    FormDeducao,
    FormMaterial,
    FormCanal
)
from src.config import globals as g
from src.utils.estilo import (
    aplicar_tema_qdarktheme,
    aplicar_tema_inicial,
    obter_temas_disponiveis,
    registrar_tema_actions,
    obter_tema_atual

)
from src.components.barra_titulo import BarraTitulo
from src.components.menu_custom import MenuCustom

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Variáveis Globais de Configuração e Versão ---
APP_VERSION = "2.2.0"  # Versão atual da aplicação
DOCUMENTS_DIR = os.path.join(os.environ["USERPROFILE"], "Documents")
CONFIG_DIR = os.path.join(DOCUMENTS_DIR, "Cálculo de Dobra")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# ID único para esta instância da aplicação
g.SESSION_ID = str(uuid.uuid4())


def verificar_admin_existente():
    """
    Verifica se existe um administrador cadastrado no banco de dados.
    Caso contrário, abre a tela de autenticação para criar um.
    """
    admin_existente = db_session.query(Usuario).filter(
        Usuario.role == "admin").first()
    if not admin_existente:
        form_aut.main(g.PRINC_FORM)


def carregar_configuracao():
    """
    Carrega a configuração do aplicativo a partir de um arquivo JSON.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def salvar_configuracao(config):
    """
    Salva a configuração do aplicativo em um arquivo JSON.
    """
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f)


# --- Funções de Gerenciamento da Aplicação e Sessão ---

def registrar_sessao():
    """Registra a sessão atual no banco de dados."""
    try:
        hostname = socket.gethostname()
        nova_sessao = SystemControl(
            type='SESSION',
            key=g.SESSION_ID,
            value=hostname
        )
        db_session.add(nova_sessao)
        db_session.commit()
        print(f"Sessão {g.SESSION_ID} registrada para {hostname}.")
    except Exception as e:
        print(f"Erro ao registrar sessão: {e}")
        db_session.rollback()


def remover_sessao():
    """Remove a sessão atual do banco de dados ao fechar."""
    try:
        sessao_para_remover = db_session.query(SystemControl).filter_by(
            key=g.SESSION_ID).first()
        if sessao_para_remover:
            db_session.delete(sessao_para_remover)
            db_session.commit()
            print(f"Sessão {g.SESSION_ID} removida.")
    except Exception as e:
        print(f"Erro ao remover sessão: {e}")
        db_session.rollback()


def verificar_comandos_sistema():
    """
    Verifica comandos do sistema (como SHUTDOWN) e atualiza o heartbeat.
    Esta função é chamada periodicamente por um QTimer.
    """
    try:
        # 1. Atualizar o heartbeat da sessão
        sessao_atual = db_session.query(SystemControl).filter_by(
            key=g.SESSION_ID).first()
        if sessao_atual:
            sessao_atual.last_updated = datetime.utcnow()
            db_session.commit()
        else:
            # Se a sessão não existe por algum motivo, registra novamente
            registrar_sessao()

        # 2. Verificar comando de desligamento
        cmd_entry = db_session.query(SystemControl).filter_by(
            key='UPDATE_CMD').first()
        if cmd_entry and cmd_entry.value == 'SHUTDOWN':
            print("Comando de desligamento recebido. Fechando a aplicação...")
            fechar_aplicativo()

    except Exception as e:
        print(f"Erro ao verificar comandos do sistema: {e}")
        db_session.rollback()


def fechar_aplicativo():
    """
    Fecha o aplicativo de forma segura, removendo a sessão.
    """
    remover_sessao()
    try:
        if g.PRINC_FORM is not None:
            g.PRINC_FORM.close()
        app = QApplication.instance()
        if app:
            app.quit()
    except (RuntimeError, AttributeError) as e:
        print(f"Erro ao fechar aplicativo: {e}")
        sys.exit(0)


def configurar_janela_principal(config):
    """
    Configura a janela principal do aplicativo com lógica melhorada.
    """
    remover_janelas_orfas()

    if g.PRINC_FORM is not None:
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
            except (ValueError, IndexError):
                pass

    icone_path = obter_caminho_icone()
    g.PRINC_FORM.setWindowIcon(QIcon(icone_path))

    def on_closing():
        remover_janelas_orfas()
        if g.PRINC_FORM is not None:
            pos = g.PRINC_FORM.pos()
            config['geometry'] = f"+{pos.x()}+{pos.y()}"
            salvar_configuracao(config)
        remover_sessao()

    def custom_close_event(event):
        try:
            on_closing()
            QApplication.instance().quit()
        except (RuntimeError, AttributeError) as e:
            print(f"Erro ao fechar aplicativo: {e}")
        finally:
            event.accept()

    g.PRINC_FORM.closeEvent = custom_close_event
    g.PRINC_FORM.setAttribute(Qt.WA_QuitOnClose, True)


def configurar_menu():
    """
    Configura o menu superior da janela principal.
    """
    if not hasattr(g, 'MENU_CUSTOM') or g.MENU_CUSTOM is None:
        return

    menu_bar = g.MENU_CUSTOM.get_menu_bar()

    _criar_menu_arquivo(menu_bar)
    _criar_menu_editar(menu_bar)
    _criar_menu_opcoes(menu_bar)
    _criar_menu_utilidades(menu_bar)
    _criar_menu_usuario(menu_bar)
    _criar_menu_ajuda(menu_bar)


def _criar_menu_arquivo(menu_bar):
    """Cria o menu Arquivo."""
    file_menu = menu_bar.addMenu("📁 Arquivo")
    acoes_arquivo = [
        ("➕ Nova Dedução", _executar_nova_deducao),
        ("➕ Novo Material", _executar_novo_material),
        ("➕ Nova Espessura", _executar_nova_espessura),
        ("➕ Novo Canal", _executar_novo_canal),
        ("separator", None),
        ("🚪 Sair", fechar_aplicativo)
    ]
    _adicionar_acoes_ao_menu(file_menu, acoes_arquivo)


def _criar_menu_editar(menu_bar):
    """Cria o menu Editar."""
    edit_menu = menu_bar.addMenu("✏️ Editar")
    acoes_editar = [
        ("📝 Editar Dedução", _executar_editar_deducao),
        ("📝 Editar Material", _executar_editar_material),
        ("📝 Editar Espessura", _executar_editar_espessura),
        ("📝 Editar Canal", _executar_editar_canal)
    ]
    _adicionar_acoes_ao_menu(edit_menu, acoes_editar)


def _criar_menu_opcoes(menu_bar):
    """Cria o menu Opções."""
    opcoes_menu = menu_bar.addMenu("⚙️ Opções")
    if not hasattr(g, 'NO_TOPO_VAR') or g.NO_TOPO_VAR is None:
        g.NO_TOPO_VAR = False

    no_topo_action = QAction("📌 No topo", g.PRINC_FORM)
    no_topo_action.setCheckable(True)
    no_topo_action.setChecked(g.NO_TOPO_VAR)
    no_topo_action.triggered.connect(_toggle_no_topo)
    opcoes_menu.addAction(no_topo_action)

    temas_disponiveis = obter_temas_disponiveis()
    temas_menu = opcoes_menu.addMenu("🎨 Temas")
    temas_actions = {}

    for tema in temas_disponiveis:
        action = QAction(tema.capitalize(), g.PRINC_FORM)
        action.setCheckable(True)
        action.setChecked(tema == getattr(g, 'TEMA_ATUAL', 'dark'))
        action.triggered.connect(
            lambda checked, t=tema: aplicar_tema_qdarktheme(t))
        temas_menu.addAction(action)
        temas_actions[tema] = action
    registrar_tema_actions(temas_actions)


def _criar_menu_utilidades(menu_bar):
    """Cria o menu Utilidades."""
    ferramentas_menu = menu_bar.addMenu("🔧 Utilidades")
    acoes_utilidades = [
        ("➗ Razão Raio/Espessura", lambda: form_razao_rie.main(g.PRINC_FORM)),
        ("🖨️ Impressão em Lote", lambda: form_impressao.main(g.PRINC_FORM))
    ]
    _adicionar_acoes_ao_menu(ferramentas_menu, acoes_utilidades)


def _criar_menu_usuario(menu_bar):
    """Cria o menu Usuário."""
    usuario_menu = menu_bar.addMenu("👤 Usuário")
    acoes_usuario = [
        ("🔐 Login", _executar_login),
        ("👥 Novo Usuário", _executar_novo_usuario),
        ("⚙️ Gerenciar Usuários", lambda: form_usuario.main(g.PRINC_FORM)),
        ("separator", None),
        ("� Sair", logout)
    ]
    _adicionar_acoes_ao_menu(usuario_menu, acoes_usuario)


def _criar_menu_ajuda(menu_bar):
    """Cria o menu Ajuda."""
    help_menu = menu_bar.addMenu("❓ Ajuda")
    sobre_action = QAction(f"ℹ️ Sobre (v{APP_VERSION})", g.PRINC_FORM)
    sobre_action.triggered.connect(lambda: form_sobre.main(g.PRINC_FORM))
    help_menu.addAction(sobre_action)


def _adicionar_acoes_ao_menu(menu, acoes):
    """Adiciona uma lista de ações a um menu."""
    for nome, funcao in acoes:
        if nome == "separator":
            menu.addSeparator()
        else:
            action = QAction(nome, g.PRINC_FORM)
            action.triggered.connect(funcao)
            menu.addAction(action)


def _executar_nova_deducao():
    setattr(g, 'EDIT_DED', False)
    FormDeducao.main(g.PRINC_FORM)


def _executar_novo_material():
    setattr(g, 'EDIT_MAT', False)
    FormMaterial.main(g.PRINC_FORM)


def _executar_nova_espessura():
    setattr(g, 'EDIT_ESP', False)
    FormEspessura.main(g.PRINC_FORM)


def _executar_novo_canal():
    setattr(g, 'EDIT_CANAL', False)
    FormCanal.main(g.PRINC_FORM)


def _executar_editar_deducao():
    setattr(g, 'EDIT_DED', True)
    FormDeducao.main(g.PRINC_FORM)


def _executar_editar_material():
    setattr(g, 'EDIT_MAT', True)
    FormMaterial.main(g.PRINC_FORM)


def _executar_editar_espessura():
    setattr(g, 'EDIT_ESP', True)
    FormEspessura.main(g.PRINC_FORM)


def _executar_editar_canal():
    setattr(g, 'EDIT_CANAL', True)
    FormCanal.main(g.PRINC_FORM)


def _executar_login():
    setattr(g, "LOGIN", True)
    form_aut.main(g.PRINC_FORM)


def _executar_novo_usuario():
    setattr(g, "LOGIN", False)
    form_aut.main(g.PRINC_FORM)


def _toggle_no_topo():
    aplicar_no_topo_app_principal()


def configurar_frames():
    """
    Configura os frames principais da janela.
    """
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


def main():
    """
    Função principal que inicializa a interface gráfica do aplicativo.
    """
    app = None
    try:
        app = QApplication(sys.argv)
        aplicar_tema_inicial("dark")

        def handle_exception(exc_type, exc_value, exc_traceback):
            if exc_type != KeyboardInterrupt:
                print("ERRO NÃO TRATADO:")
                print(''.join(traceback.format_exception(
                    exc_type, exc_value, exc_traceback)))

        def signal_handler(signum, frame):
            print(f"Sinal recebido: {signum}")
            fechar_aplicativo()

        sys.excepthook = handle_exception
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        config = carregar_configuracao()
        configurar_janela_principal(config)
        configurar_frames()
        configurar_menu()

        # Registrar esta sessão no banco de dados
        registrar_sessao()

        verificar_admin_existente()

        if g.PRINC_FORM is not None:
            g.PRINC_FORM.show()

            # Iniciar timer para verificar comandos e atualizar heartbeat
            g.timer_sistema = QTimer()
            g.timer_sistema.timeout.connect(verificar_comandos_sistema)
            g.timer_sistema.start(5000)  # Verifica a cada 5 segundos

            print("Aplicativo iniciado com sucesso!")
            app.aboutToQuit.connect(remover_sessao)
            return app.exec()

        print("ERRO: Janela principal não foi criada!")
        return 1

    except KeyboardInterrupt:
        print("Aplicativo interrompido pelo usuário")
        if app:
            app.quit()
        return 0
    except Exception as e:
        print(f"ERRO CRÍTICO na inicialização: {e}")
        traceback.print_exc()
        if app:
            app.quit()
        return 1
    finally:
        # Garante que a sessão seja removida em caso de falha na inicialização
        if 'g' in globals() and hasattr(g, 'SESSION_ID'):
            remover_sessao()
        if db_session:
            db_session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
