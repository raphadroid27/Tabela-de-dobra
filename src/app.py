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
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout)  # type: ignore
from PySide6.QtCore import Qt  # type: ignore
from PySide6.QtGui import QIcon, QAction  # type: ignore

from src.utils.utilitarios import obter_caminho_icone
from src.utils.usuarios import logout
from src.utils.janelas import (
    aplicar_no_topo_app_principal, cleanup_orphaned_windows)
from src.utils.interface_manager import carregar_interface
from src.utils.interface import aplicar_medida_borda_espaco
from src.utils.banco_dados import session
from src.models import Usuario
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

DOCUMENTS_DIR = os.path.join(os.environ["USERPROFILE"], "Documents")
CONFIG_DIR = os.path.join(DOCUMENTS_DIR, "Cálculo de Dobra")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def verificar_admin_existente():
    """
    Verifica se existe um administrador cadastrado no banco de dados.
    Caso contrário, abre a tela de autenticação para criar um.
    """
    admin_existente = session.query(Usuario).filter(
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


def fechar_aplicativo():
    """
    Fecha o aplicativo de forma segura.
    """
    try:
        if g.PRINC_FORM is not None:
            g.PRINC_FORM.close()
        app = QApplication.instance()
        if app:
            app.quit()
    except (RuntimeError, AttributeError) as e:
        print(f"Erro ao fechar aplicativo: {e}")
        # Forçar o fechamento se necessário
        sys.exit(0)


def configurar_janela_principal(config):
    """
    Configura a janela principal do aplicativo com lógica melhorada.
    """
    # Garantir que existe apenas uma janela principal e limpar órfãs
    cleanup_orphaned_windows()

    if g.PRINC_FORM is not None:
        try:
            g.PRINC_FORM.close()
            g.PRINC_FORM.deleteLater()
            g.PRINC_FORM = None
        except (RuntimeError, AttributeError):
            pass

    g.PRINC_FORM = QMainWindow()
    g.PRINC_FORM.setWindowTitle("Cálculo de Dobra")
    g.PRINC_FORM.setFixedSize(340, 500)
    g.PRINC_FORM.is_main_window = True

    # Remover barra de título nativa e borda
    g.PRINC_FORM.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

    if 'geometry' in config and isinstance(config['geometry'], str):
        # Parse geometry string and apply
        parts = config['geometry'].split('+')
        if len(parts) >= 3:
            try:
                x, y = int(parts[1]), int(parts[2])
                g.PRINC_FORM.move(x, y)
            except (ValueError, IndexError):
                # Se não conseguir fazer o parse, usa posição padrão
                pass

    icone_path = obter_caminho_icone()
    g.PRINC_FORM.setWindowIcon(QIcon(icone_path))

    def on_closing():
        cleanup_orphaned_windows()
        if g.PRINC_FORM is not None:
            pos = g.PRINC_FORM.pos()
            config['geometry'] = f"+{pos.x()}+{pos.y()}"
            salvar_configuracao(config)

    # Criar uma função personalizada para o evento de fechamento
    def custom_close_event(event):
        try:
            on_closing()
            # Garantir que a aplicação seja encerrada quando a janela principal for fechada
            QApplication.instance().quit()
        except (RuntimeError, AttributeError) as e:
            print(f"Erro ao fechar aplicativo: {e}")
        finally:
            event.accept()

    # Sobrescrever o closeEvent
    g.PRINC_FORM.closeEvent = custom_close_event

    # Configurar para encerrar a aplicação quando a janela principal for fechada
    g.PRINC_FORM.setAttribute(Qt.WA_QuitOnClose, True)


def configurar_menu():
    """
    Configura o menu superior da janela principal.
    """
    if not hasattr(g, 'MENU_CUSTOM') or g.MENU_CUSTOM is None:
        return

    menu_bar = g.MENU_CUSTOM.get_menu_bar()

    # Criar menus usando funções especializadas
    _criar_menu_arquivo(menu_bar)
    _criar_menu_editar(menu_bar)
    _criar_menu_opcoes(menu_bar)
    _criar_menu_utilidades(menu_bar)
    _criar_menu_usuario(menu_bar)
    _criar_menu_ajuda(menu_bar)


def _criar_menu_arquivo(menu_bar):
    """Cria o menu Arquivo."""
    file_menu = menu_bar.addMenu("📁 Arquivo")

    # Definir ações e suas funções
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

    # Inicializar NO_TOPO_VAR se não existir
    if not hasattr(g, 'NO_TOPO_VAR') or g.NO_TOPO_VAR is None:
        g.NO_TOPO_VAR = False

    no_topo_action = QAction("📌 No topo", g.PRINC_FORM)
    no_topo_action.setCheckable(True)
    no_topo_action.setChecked(g.NO_TOPO_VAR)
    no_topo_action.triggered.connect(_toggle_no_topo)
    opcoes_menu.addAction(no_topo_action)

    # Adicionar submenu Temas
    temas_disponiveis = obter_temas_disponiveis()
    temas_menu = opcoes_menu.addMenu("🎨 Temas")

    # Inicializar dicionário para rastrear ações dos temas
    temas_actions = {}

    # Criar ações para cada tema
    for tema in temas_disponiveis:
        action = QAction(tema.capitalize(), g.PRINC_FORM)
        action.setCheckable(True)
        action.setChecked(tema == getattr(g, 'TEMA_ATUAL', 'dark'))
        action.triggered.connect(
            lambda checked, t=tema: aplicar_tema_qdarktheme(t))
        temas_menu.addAction(action)
        temas_actions[tema] = action

    # Registrar actions no módulo de estilo para controle de estado
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
        ("🚪 Sair", logout)
    ]

    _adicionar_acoes_ao_menu(usuario_menu, acoes_usuario)


def _criar_menu_ajuda(menu_bar):
    """Cria o menu Ajuda."""
    help_menu = menu_bar.addMenu("❓ Ajuda")

    sobre_action = QAction("ℹ️ Sobre", g.PRINC_FORM)
    sobre_action.triggered.connect(lambda: form_sobre.main(g.PRINC_FORM))
    help_menu.addAction(sobre_action)


def _adicionar_acoes_ao_menu(menu, acoes):
    """
    Adiciona uma lista de ações a um menu.
    Args:
        menu: O menu onde adicionar as ações
        acoes: Lista de tuplas (nome, função) ou ("separator", None)
    """
    for nome, funcao in acoes:
        if nome == "separator":
            menu.addSeparator()
        else:
            action = QAction(nome, g.PRINC_FORM)
            action.triggered.connect(funcao)
            menu.addAction(action)

# Funções auxiliares para as ações dos menus


def _executar_nova_deducao():
    """Executa a ação de nova dedução."""
    setattr(g, 'EDIT_DED', False)
    FormDeducao.main(g.PRINC_FORM)


def _executar_novo_material():
    """Executa a ação de novo material."""
    setattr(g, 'EDIT_MAT', False)
    FormMaterial.main(g.PRINC_FORM)


def _executar_nova_espessura():
    """Executa a ação de nova espessura."""
    setattr(g, 'EDIT_ESP', False)
    FormEspessura.main(g.PRINC_FORM)


def _executar_novo_canal():
    """Executa a ação de novo canal."""
    setattr(g, 'EDIT_CANAL', False)
    FormCanal.main(g.PRINC_FORM)


def _executar_editar_deducao():
    """Executa a ação de editar dedução."""
    setattr(g, 'EDIT_DED', True)
    FormDeducao.main(g.PRINC_FORM)


def _executar_editar_material():
    """Executa a ação de editar material."""
    setattr(g, 'EDIT_MAT', True)
    FormMaterial.main(g.PRINC_FORM)


def _executar_editar_espessura():
    """Executa a ação de editar espessura."""
    setattr(g, 'EDIT_ESP', True)
    FormEspessura.main(g.PRINC_FORM)


def _executar_editar_canal():
    """Executa a ação de editar canal."""
    setattr(g, 'EDIT_CANAL', True)
    FormCanal.main(g.PRINC_FORM)


def _executar_login():
    """Executa a ação de login."""
    setattr(g, "LOGIN", True)
    form_aut.main(g.PRINC_FORM)


def _executar_novo_usuario():
    """Executa a ação de novo usuário."""
    setattr(g, "LOGIN", False)
    form_aut.main(g.PRINC_FORM)


def _toggle_no_topo():
    """Função para alternar o estado 'no topo' e sincronizar o checkbox."""
    aplicar_no_topo_app_principal()


def configurar_frames():
    """
    Configura os frames principais da janela.
    """
    central_widget = QWidget()
    g.PRINC_FORM.setCentralWidget(central_widget)

    # Layout vertical para barra de título customizada, menu customizado e conteúdo
    vlayout = QVBoxLayout(central_widget)
    aplicar_medida_borda_espaco(vlayout, 0, 0)

    # Barra de título customizada
    tema_atual = getattr(g, 'TEMA_ATUAL', 'dark')
    g.BARRA_TITULO = BarraTitulo(g.PRINC_FORM, tema=tema_atual)
    vlayout.addWidget(g.BARRA_TITULO)
    # Forçar atualização da cor da barra após aplicar o tema inicial
    if hasattr(g, 'BARRA_TITULO') and g.BARRA_TITULO:
        g.BARRA_TITULO.set_tema(obter_tema_atual())

    # Menu customizado
    g.MENU_CUSTOM = MenuCustom(g.PRINC_FORM)
    vlayout.addWidget(g.MENU_CUSTOM)

    # Widget de conteúdo principal
    conteudo_widget = QWidget()
    layout = QGridLayout(conteudo_widget)
    vlayout.addWidget(conteudo_widget)

    g.VALORES_W = [1]
    g.EXP_V = False  # Convertido de IntVar para bool
    g.EXP_H = False  # Convertido de IntVar para bool

    # Armazenar referência ao layout principal
    g.MAIN_LAYOUT = layout

    # Atribuir a função carregar_interface à variável global
    g.CARREGAR_INTERFACE_FUNC = carregar_interface

    carregar_interface(1, layout)


def main():
    """
    Função principal que inicializa a interface gráfica do aplicativo.
    """

    app = None
    try:
        app = QApplication(sys.argv)

        # Aplicar tema inicial com correções CSS
        aplicar_tema_inicial("dark")

        # Configurar para capturar exceções não tratadas
        def handle_exception(exc_type, exc_value, exc_traceback):
            if exc_type != KeyboardInterrupt:
                print("ERRO NÃO TRATADO:")
                print(''.join(traceback.format_exception(
                    exc_type, exc_value, exc_traceback)))

        def signal_handler(signum):
            print(f"Sinal recebido: {signum}")
            if app:
                app.quit()
            sys.exit(0)

        sys.excepthook = handle_exception
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        print("Carregando configuração...")
        config = carregar_configuracao()

        print("Configurando janela principal...")
        configurar_janela_principal(config)

        print("Configurando frames...")
        configurar_frames()

        print("Configurando menu...")
        configurar_menu()

        print("Verificando admin existente...")
        verificar_admin_existente()

        if g.PRINC_FORM is not None:
            print("Exibindo janela principal...")
            g.PRINC_FORM.show()

            print("Aplicativo iniciado com sucesso!")

            def on_app_exit():
                pass

            app.aboutToQuit.connect(on_app_exit)

            return app.exec()

        print("ERRO: Janela principal não foi criada!")
        return 1

    except KeyboardInterrupt:
        print("Aplicativo interrompido pelo usuário")
        if app:
            app.quit()
        return 0

    except (RuntimeError, ImportError, AttributeError, OSError) as e:
        print(f"ERRO CRÍTICO na inicialização: {e}")
        traceback.print_exc()
        if app:
            app.quit()
        return 1

    except Exception as e:  # pylint: disable=broad-except
        print(f"ERRO INESPERADO na inicialização: {e}")
        traceback.print_exc()
        if app:
            app.quit()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
