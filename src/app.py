'''
# Formulário Principal do Aplicativo de Cálculo de Dobra
# Este módulo implementa a interface principal do aplicativo, permitindo a
# gestão de deduções, materiais, espessuras e canais. Ele utiliza a biblioteca
# tkinter para a interface gráfica, o módulo globals para variáveis globais,
# e outros módulos auxiliares para operações relacionadas ao banco de dados
# e funcionalidades específicas.
'''

import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Desativa o aviso do pylint para importações fora de ordem
# pylint: disable=wrong-import-position
import json
import tkinter as tk
from src.utils.banco_dados import session
from src.models import Usuario
from src.components.dobra_90 import DobraUI
from src.components.botoes import criar_botoes
from src.forms import (
    form_espessura,
    form_deducao,
    form_material,
    form_canal,
    form_sobre,
    form_aut,
    form_usuario,
    form_razao_rie
)
from src.components.cabecalho import CabecalhoUI
from src.components.avisos import AvisosUI
from src.config import globals as g
from src.utils.janelas import no_topo
from src.utils.interface import (salvar_valores_cabecalho,
                                 salvar_valores_dobra,
                                 restaurar_valores_cabecalho,
                                 restaurar_valores_dobra,
                                 todas_funcoes
                                 )
from src.utils.utilitarios import obter_caminho_icone
from src.utils.usuarios import logout
# pylint: enable=wrong-import-position

DOCUMENTS_DIR = os.path.join(os.environ["USERPROFILE"], "Documents")
CONFIG_DIR = os.path.join(DOCUMENTS_DIR, "Cálculo de Dobra")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class AppUI:
    def __init__(self):
        self.janela_principal = None
        self.frame_superior = None
        self.cabecalho_ui = None
        self.dobras_ui = {}  # Dicionário para armazenar múltiplas colunas de dobra
        self.botoes_ui = None
        self.frame_botoes = None
        self.avisos_ui = None
        
        # Estados de expansão - serão inicializados após criar a janela principal
        self.expandir_v = None
        self.expandir_h = None
        
        # Valores de largura das colunas
        self.valores_w = [1, 2]

    def inicializar_variaveis(self):
        '''
        Inicializa as variáveis Tkinter após a criação da janela principal.
        '''
        self.expandir_v = tk.IntVar()
        self.expandir_h = tk.IntVar()

def verificar_admin_existente():
    '''
    Verifica se existe um administrador cadastrado no banco de dados.
    Caso contrário, abre a tela de autenticação para criar um.
    '''
    admin_existente = session.query(Usuario).filter(Usuario.role == "admin").first()
    if not admin_existente:
        form_aut.main(g.PRINC_FORM)


def carregar_configuracao():
    '''
    Carrega a configuração do aplicativo a partir de um arquivo JSON.
    '''
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def salvar_configuracao(config):
    '''
    Salva a configuração do aplicativo em um arquivo JSON.
    '''
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f)


def form_true(form, editar_attr, root):
    '''
    Abre o formulário de edição de um item específico
    (dedução, material, espessura ou canal).
    '''
    setattr(g, editar_attr, True)
    form.main(root)

def form_false(form, editar_attr, root):
    '''
    Fecha o formulário de edição de um item específico
    (dedução, material, espessura ou canal).
    '''
    setattr(g, editar_attr, False)
    form.main(root)

def carregar_interface(app_instance=None):
    '''
    Atualiza o cabeçalho e recria os widgets no frame de dobras.
    '''
    # Se não foi passada uma instância, usa a global
    if app_instance is None:
        app_instance = app
      # Salvar os valores dos widgets do cabeçalho se já existir um
    if hasattr(app_instance, 'cabecalho_ui') and app_instance.cabecalho_ui:
        salvar_valores_cabecalho(app_instance.cabecalho_ui)
    
    # Salvar os valores das dobras se já existirem
    if hasattr(app_instance, 'dobras_ui') and app_instance.dobras_ui:
        for w in app_instance.valores_w:
            if w in app_instance.dobras_ui:
                salvar_valores_dobra(app_instance.dobras_ui[w], w)
    
    # Limpar widgets antigos no frame superior
    for widget in app_instance.frame_superior.winfo_children():
        widget.destroy()

    # Determinar número de dobras baseado na expansão vertical
    numero_dobras = 10 if app_instance.expandir_v.get() == 1 else 5
    
    # Determinar valores de largura baseado na expansão horizontal
    app_instance.valores_w = [1, 2] if app_instance.expandir_h.get() == 1 else [1]

    # Criar cabeçalho principal
    app_instance.cabecalho_ui = CabecalhoUI(app_instance.frame_superior, None)
    app_instance.cabecalho_ui.frame.grid(row=0, column=0, sticky='ewns', ipadx=2, ipady=2)    # Adicionar avisos se expansão horizontal estiver ativa
    if app_instance.expandir_h.get() == 1:
        app_instance.avisos_ui = AvisosUI(app_instance.frame_superior)
        app_instance.avisos_ui.frame.grid(row=0, column=1, sticky='ewns', ipadx=2, ipady=2)

    # Criar colunas de dobras baseado nos valores_w
    app_instance.dobras_ui = {}
    for w in app_instance.valores_w:
        dobra_ui = DobraUI(app_instance.cabecalho_ui, app_instance.frame_superior, w)
        dobra_ui.entradas_dobras(app_instance.cabecalho_ui, numero_dobras, w)
        dobra_ui.frame.grid(row=1, column=w-1, sticky='ewns', ipadx=2, ipady=2)
        app_instance.dobras_ui[w] = dobra_ui

    # Atualizar referência no cabeçalho para a primeira coluna de dobras
    if app_instance.dobras_ui:
        app_instance.cabecalho_ui.dobras_ui = app_instance.dobras_ui[1]

    # Criar botões
    app_instance.frame_botoes = criar_botoes(app_instance.frame_superior, app_instance)
    columnspan = len(app_instance.valores_w)
    app_instance.frame_botoes.grid(row=2, column=0, sticky='ewns', ipadx=2, ipady=2, columnspan=columnspan)

    # Configurar grid weights para as colunas
    for i, w in enumerate(app_instance.valores_w):
        app_instance.frame_superior.columnconfigure(i, weight=1)    # Restaurar valores
    for w in app_instance.valores_w:
        if w in app_instance.dobras_ui:
            restaurar_valores_dobra(app_instance.dobras_ui[w], w)
    
    restaurar_valores_cabecalho(app_instance.cabecalho_ui)
    
    # Chamar todas_funcoes para cada coluna de dobra criada
    for w in app_instance.valores_w:
        if w in app_instance.dobras_ui:
            todas_funcoes(app_instance.cabecalho_ui, app_instance.dobras_ui[w])

def configurar_janela_principal(config):
    '''
    Configura a janela principal do aplicativo.
    '''
    app.janela_principal = tk.Tk()
    app.janela_principal.title("Cálculo de Dobra")
    app.janela_principal.geometry('340x400')
    if 'geometry' in config:
        app.janela_principal.geometry(config['geometry'])
    app.janela_principal.resizable(False, False)
    app.janela_principal.update_idletasks()

    # Inicializar as variáveis Tkinter após criar a janela
    app.inicializar_variaveis()

    icone_path = obter_caminho_icone()
    app.janela_principal.iconbitmap(icone_path)

    def on_closing():
        geometry = app.janela_principal.geometry()
        position = geometry.split('+')[1:]
        config['geometry'] = f"+{position[0]}+{position[1]}"
        salvar_configuracao(config)
        app.janela_principal.destroy()

    app.janela_principal.protocol("WM_DELETE_WINDOW", on_closing)

def configurar_menu():
    '''
    Configura o menu superior da janela principal.
    '''
    menu_bar = tk.Menu(app.janela_principal)
    app.janela_principal.config(menu=menu_bar)

    # Menu Arquivo
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Arquivo", menu=file_menu)
    file_menu.add_command(label="Nova Dedução", command=lambda: form_false(form_deducao,
                                                                           'EDIT_DED',
                                                                           app.janela_principal))

    file_menu.add_command(label="Novo Material", command=lambda: form_false(form_material,
                                                                            'EDIT_MAT',
                                                                            app.janela_principal))

    file_menu.add_command(label="Nova Espessura", command=lambda: form_false(form_espessura,
                                                                           'EDIT_ESP',
                                                                           app.janela_principal))

    file_menu.add_command(label="Novo Canal", command=lambda: form_false(form_canal,
                                                                       'EDIT_CANAL',
                                                                       app.janela_principal))
    file_menu.add_separator()
    file_menu.add_command(label="Sair", command=app.janela_principal.destroy)

    # Menu Editar
    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Editar", menu=edit_menu)
    edit_menu.add_command(label="Editar Dedução", command=lambda: form_true(form_deducao,
                                                                           'EDIT_DED',
                                                                           app.janela_principal))

    edit_menu.add_command(label="Editar Material", command=lambda: form_true(form_material,
                                                                           'EDIT_MAT',
                                                                           app.janela_principal))

    edit_menu.add_command(label="Editar Espessura", command=lambda: form_true(form_espessura,
                                                                           'EDIT_ESP',
                                                                           app.janela_principal))

    edit_menu.add_command(label="Editar Canal", command=lambda: form_true(form_canal,
                                                                       'EDIT_CANAL',
                                                                       app.janela_principal))

    # Menu Opções
    opcoes_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Opções", menu=opcoes_menu)
    g.NO_TOPO_VAR = tk.IntVar()
    opcoes_menu.add_checkbutton(label="No topo", variable=g.NO_TOPO_VAR,
                                command=lambda: no_topo(app.janela_principal))

    # Menu ferramentas
    ferramentas_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ferramentas", menu=ferramentas_menu)
    ferramentas_menu.add_command(label="Razão Raio/Espessura",
                                 command=lambda: form_razao_rie.main(app.janela_principal))

    # Menu Usuário
    usuario_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Usuário", menu=usuario_menu)
    usuario_menu.add_command(label="Login", command=lambda: form_true(form_aut,
                                                                      "LOGIN",
                                                                      app.janela_principal))

    usuario_menu.add_command(label="Novo Usuário", command=lambda: form_false(form_aut,
                                                                           "LOGIN",
                                                                           app.janela_principal))

    usuario_menu.add_command(label="Gerenciar Usuários",
                             command=lambda: form_usuario.main(app.janela_principal))
    usuario_menu.add_separator()
    usuario_menu.add_command(label="Sair", command=logout)

    # Menu Ajuda
    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ajuda", menu=help_menu)
    help_menu.add_command(label="Sobre", command=lambda: form_sobre.main(app.janela_principal))

def configurar_frames():
    '''
    Configura os frames principais da janela.
    '''
    app.frame_superior = tk.LabelFrame(app.janela_principal)
    app.frame_superior.pack(fill='both', expand=True, padx=10, pady=10)

    app.frame_superior.columnconfigure(0, weight=1)
    app.frame_superior.rowconfigure(0, weight=1)
    app.frame_superior.rowconfigure(1, weight=1)
    app.frame_superior.rowconfigure(2, weight=1)

    carregar_interface()

def main():
    '''
    Função principal que inicializa a interface gráfica do aplicativo.
    '''
    global app
    app = AppUI()
    
    config = carregar_configuracao()
    configurar_janela_principal(config)
    configurar_menu()
    configurar_frames()
    verificar_admin_existente()
    app.janela_principal.mainloop()

if __name__ == "__main__":
    main()
