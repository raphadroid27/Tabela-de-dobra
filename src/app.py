"""
Formulário Principal do Aplicativo de Cálculo de Dobra
Este módulo implementa a interface principal do aplicativo, permitindo a
gestão de deduções, materiais, espessuras e canais. Ele utiliza a biblioteca
PySide6 para a interface gráfica, o módulo globals para variáveis globais,
e outros módulos auxiliares para operações relacionadas ao banco de dados
e funcionalidades específicas.
"""

import json
import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMenuBar, QLabel, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Desativa o aviso do pylint para importações fora de ordem
# pylint: disable=wrong-import-position

from src.config import globals as g
from src.forms import (
    form_espessura,
    form_deducao,
    form_material,
    form_canal,
    form_sobre,
    form_aut,
    form_usuario,
    form_razao_rie,
    form_impressao
)
from src.models import Usuario
from src.utils.banco_dados import session
from src.utils.interface_manager import carregar_interface
from src.utils.janelas import no_topo
from src.utils.usuarios import logout
from src.utils.utilitarios import obter_caminho_icone

# pylint: enable=wrong-import-position

DOCUMENTS_DIR = os.path.join(os.environ["USERPROFILE"], "Documents")
CONFIG_DIR = os.path.join(DOCUMENTS_DIR, "Cálculo de Dobra")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def verificar_admin_existente():
    """
    Verifica se existe um administrador cadastrado no banco de dados.
    Caso contrário, abre a tela de autenticação para criar um.
    """
    admin_existente = session.query(Usuario).filter(Usuario.role == "admin").first()
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


def form_true(form, editar_attr, root):
    """
    Abre o formulário de edição de um item específico
    (dedução, material, espessura ou canal).
    """
    setattr(g, editar_attr, True)
    form.main(root)


def form_false(form, editar_attr, root):
    """
    Fecha o formulário de edição de um item específico
    (dedução, material, espessura ou canal).
    """
    setattr(g, editar_attr, False)
    form.main(root)


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
            
    except Exception as e:
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
        except:
            pass
    
    g.PRINC_FORM = QMainWindow()
    g.PRINC_FORM.setWindowTitle("Cálculo de Dobra")
    g.PRINC_FORM.resize(340, 400)
    
    # Marcar como janela principal para identificação
    g.PRINC_FORM._is_main_window = True
    
    # Definir tamanhos mínimos e máximos para garantir redimensionamento correto
    g.PRINC_FORM.setMinimumSize(340, 400)  # Tamanho mínimo = tamanho sem expansão
    g.PRINC_FORM.setMaximumSize(680, 500)  # Tamanho máximo = tamanho com ambas expansões
    
    # Configurar flags da janela corretamente
    # Garantir que todos os botões da barra de título estejam habilitados
    window_flags = (Qt.Window | 
                   Qt.WindowTitleHint | 
                   Qt.WindowSystemMenuHint | 
                   Qt.WindowMinimizeButtonHint | 
                   Qt.WindowMaximizeButtonHint | 
                   Qt.WindowCloseButtonHint)
    g.PRINC_FORM.setWindowFlags(window_flags)
    
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
        except Exception as e:
            print(f"Erro ao fechar aplicativo: {e}")
        finally:
            event.accept()

    # Sobrescrever o closeEvent
    g.PRINC_FORM.closeEvent = custom_close_event
    
    # Configurar para encerrar a aplicação quando a janela principal for fechada
    g.PRINC_FORM.setAttribute(Qt.WA_QuitOnClose, True)


def cleanup_orphaned_windows():
    """
    Remove todas as janelas órfãs que possam estar abertas.
    """
    try:
        app = QApplication.instance()
        if not app:
            return
        
        main_window = g.PRINC_FORM if hasattr(g, 'PRINC_FORM') else None
        top_level_widgets = app.topLevelWidgets()
        
        for widget in top_level_widgets[:]:  # Cópia para iteração segura
            if (widget != main_window and 
                widget.isVisible() and 
                not hasattr(widget, '_is_system_widget') and
                not hasattr(widget, '_is_main_window')):
                
                widget_type = type(widget).__name__
                if widget_type in ['QLabel', 'QFrame', 'QWidget', 'QDialog', 'QWindow', 'QMainWindow']:
                    try:
                        widget.hide()
                        widget.close()
                        widget.deleteLater()
                    except:
                        pass
        
        # Processar eventos para garantir limpeza
        app.processEvents()
        
    except:
        pass


def configurar_menu():
    """
    Configura o menu superior da janela principal.
    """
    if g.PRINC_FORM is None:
        return

    menu_bar = g.PRINC_FORM.menuBar()

    # Menu Arquivo
    file_menu = menu_bar.addMenu("Arquivo")

    nova_deducao_action = QAction("Nova Dedução", g.PRINC_FORM)
    nova_deducao_action.triggered.connect(lambda: form_false(form_deducao, 'EDIT_DED', g.PRINC_FORM))
    file_menu.addAction(nova_deducao_action)

    novo_material_action = QAction("Novo Material", g.PRINC_FORM)
    novo_material_action.triggered.connect(lambda: form_false(form_material, 'EDIT_MAT', g.PRINC_FORM))
    file_menu.addAction(novo_material_action)

    nova_espessura_action = QAction("Nova Espessura", g.PRINC_FORM)
    nova_espessura_action.triggered.connect(lambda: form_false(form_espessura, 'EDIT_ESP', g.PRINC_FORM))
    file_menu.addAction(nova_espessura_action)

    novo_canal_action = QAction("Novo Canal", g.PRINC_FORM)
    novo_canal_action.triggered.connect(lambda: form_false(form_canal, 'EDIT_CANAL', g.PRINC_FORM))
    file_menu.addAction(novo_canal_action)

    file_menu.addSeparator()
    
    sair_action = QAction("Sair", g.PRINC_FORM)
    sair_action.triggered.connect(fechar_aplicativo)
    file_menu.addAction(sair_action)

    # Menu Editar
    edit_menu = menu_bar.addMenu("Editar")
    
    editar_deducao_action = QAction("Editar Dedução", g.PRINC_FORM)
    editar_deducao_action.triggered.connect(lambda: form_true(form_deducao, 'EDIT_DED', g.PRINC_FORM))
    edit_menu.addAction(editar_deducao_action)

    editar_material_action = QAction("Editar Material", g.PRINC_FORM)
    editar_material_action.triggered.connect(lambda: form_true(form_material, 'EDIT_MAT', g.PRINC_FORM))
    edit_menu.addAction(editar_material_action)

    editar_espessura_action = QAction("Editar Espessura", g.PRINC_FORM)
    editar_espessura_action.triggered.connect(lambda: form_true(form_espessura, 'EDIT_ESP', g.PRINC_FORM))
    edit_menu.addAction(editar_espessura_action)

    editar_canal_action = QAction("Editar Canal", g.PRINC_FORM)
    editar_canal_action.triggered.connect(lambda: form_true(form_canal, 'EDIT_CANAL', g.PRINC_FORM))
    edit_menu.addAction(editar_canal_action)

    # Menu Opções
    opcoes_menu = menu_bar.addMenu("Opções")
    g.NO_TOPO_VAR = False  # Convertido de IntVar para bool
    no_topo_action = QAction("No topo", g.PRINC_FORM)
    no_topo_action.setCheckable(True)
    no_topo_action.triggered.connect(lambda: no_topo(g.PRINC_FORM))
    opcoes_menu.addAction(no_topo_action)

    # Menu ferramentas
    ferramentas_menu = menu_bar.addMenu("Utilidades")
    
    razao_action = QAction("Razão Raio/Espessura", g.PRINC_FORM)
    razao_action.triggered.connect(lambda: form_razao_rie.main(g.PRINC_FORM))
    ferramentas_menu.addAction(razao_action)
    
    impressao_action = QAction("Impressão em Lote", g.PRINC_FORM)
    impressao_action.triggered.connect(lambda: form_impressao.main(g.PRINC_FORM))
    ferramentas_menu.addAction(impressao_action)

    # Menu Usuário
    usuario_menu = menu_bar.addMenu("Usuário")
    
    login_action = QAction("Login", g.PRINC_FORM)
    login_action.triggered.connect(lambda: form_true(form_aut, "LOGIN", g.PRINC_FORM))
    usuario_menu.addAction(login_action)

    novo_usuario_action = QAction("Novo Usuário", g.PRINC_FORM)
    novo_usuario_action.triggered.connect(lambda: form_false(form_aut, "LOGIN", g.PRINC_FORM))
    usuario_menu.addAction(novo_usuario_action)

    gerenciar_usuarios_action = QAction("Gerenciar Usuários", g.PRINC_FORM)
    gerenciar_usuarios_action.triggered.connect(lambda: form_usuario.main(g.PRINC_FORM))
    usuario_menu.addAction(gerenciar_usuarios_action)
    
    usuario_menu.addSeparator()
    
    sair_usuario_action = QAction("Sair", g.PRINC_FORM)
    sair_usuario_action.triggered.connect(logout)
    usuario_menu.addAction(sair_usuario_action)

    # Menu Ajuda
    help_menu = menu_bar.addMenu("Ajuda")
    
    sobre_action = QAction("Sobre", g.PRINC_FORM)
    sobre_action.triggered.connect(lambda: form_sobre.main(g.PRINC_FORM))
    help_menu.addAction(sobre_action)


def configurar_frames():
    """
    Configura os frames principais da janela.
    """
    central_widget = QWidget()
    g.PRINC_FORM.setCentralWidget(central_widget)
    
    layout = QGridLayout(central_widget)  # Mudado para QGridLayout
    layout.setContentsMargins(10, 10, 10, 10)

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
        
        # Configurar para capturar exceções não tratadas
        import traceback
        import signal
        
        def handle_exception(exc_type, exc_value, exc_traceback):
            """Captura exceções não tratadas"""
            if exc_type != KeyboardInterrupt:
                print("ERRO NÃO TRATADO:")
                print(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            
        def signal_handler(signum, frame):
            """Handler para sinais do sistema"""
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
        
        print("Configurando menu...")
        configurar_menu()
        
        print("Configurando frames...")
        configurar_frames()
        
        print("Verificando admin existente...")
        verificar_admin_existente()
        
        if g.PRINC_FORM is not None:
            print("Exibindo janela principal...")
            g.PRINC_FORM.show()
            print("Aplicativo iniciado com sucesso!")
            
            # Adicionar uma função para capturar quando a janela é fechada
            def on_app_exit():
                print("Aplicativo sendo finalizado...")
                
            app.aboutToQuit.connect(on_app_exit)
            
            exit_code = app.exec()
            print(f"Aplicativo finalizado com código: {exit_code}")
            return exit_code
        else:
            print("ERRO: Janela principal não foi criada!")
            return 1
            
    except KeyboardInterrupt:
        print("Aplicativo interrompido pelo usuário")
        if app:
            app.quit()
        return 0
    except Exception as e:
        print(f"ERRO CRÍTICO na inicialização: {e}")
        import traceback
        traceback.print_exc()
        if app:
            app.quit()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
