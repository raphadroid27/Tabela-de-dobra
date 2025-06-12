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
from src.components.dobra_90 import InterfaceDobra
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
from src.components.cabecalho import InterfaceCabecalho
from src.components.avisos import InterfaceAvisos
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

class InterfaceApp:
    def __init__(self):

        '''
        Configura a janela principal do aplicativo.
        '''
        self.janela_principal = tk.Tk()
        self.janela_principal.title("Cálculo de Dobra")
        self.janela_principal.geometry('340x400')
        
        # Carregar configuração antes de usar
        config = carregar_configuracao()
        if 'geometry' in config:
            self.janela_principal.geometry(config['geometry'])
        self.janela_principal.resizable(False, False)
        self.janela_principal.update_idletasks()        # Inicializar as variáveis Tkinter após criar a janela

        icone_path = obter_caminho_icone()
        self.janela_principal.iconbitmap(icone_path)

        self.dobras_ui = {}
        '''
        Configura os frames principais da janela.
        '''
        self.frame_superior = tk.LabelFrame(self.janela_principal)
        self.frame_superior.pack(fill='both', expand=True, padx=10, pady=10)

        for i in range(3):
            self.frame_superior.rowconfigure(i, weight=1)
        self.frame_superior.columnconfigure(0, weight=1)

        # Inicializar as variáveis de expansão
        self.expandir_v = tk.IntVar()
        self.expandir_h = tk.IntVar()
          # Valores de largura das colunas
        self.valores_w = [1, 2]

        # Dicionário para rastrear formulários abertos
        self.formularios_abertos = {}

        self.cabecalho_ui = InterfaceCabecalho(self.frame_superior, None)

def verificar_admin_existente(app_principal):
    '''
    Verifica se existe um administrador cadastrado no banco de dados.
    Caso contrário, abre a tela de autenticação para criar um.
    '''
    admin_existente = session.query(Usuario).filter(Usuario.role == "admin").first()
    if not admin_existente:
        abrir_form_aut(app_principal.janela_principal, app_principal, login=False)

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

def verificar_formulario_aberto(nome_formulario):
    '''
    Verifica se um formulário já está aberto e o foca se estiver.
    Retorna True se o formulário já está aberto, False caso contrário.
    '''
    if nome_formulario in app.formularios_abertos:
        janela_ou_flag = app.formularios_abertos[nome_formulario]
        
        # Se for apenas True (flag), assumir que está aberto
        if janela_ou_flag is True:
            return True
            
        # Se for uma janela, verificar se ainda existe
        try:
            # Verifica se a janela ainda existe
            janela_ou_flag.winfo_exists()
            # Se existe, traz para frente e foca
            janela_ou_flag.lift()
            janela_ou_flag.focus_force()
            return True
        except (tk.TclError, AttributeError):
            # Se a janela não existe mais, remove do dicionário
            del app.formularios_abertos[nome_formulario]
            return False
    return False

def form_true(form, editar_attr, root):
    '''
    Abre o formulário de edição de um item específico
    (dedução, material, espessura ou canal).
    '''
    # Determinar nome do formulário baseado no módulo
    nome_formulario = f"{form.__name__}_edicao"
    
    # Verificar se o formulário já está aberto
    if verificar_formulario_aberto(nome_formulario):
        return
    
    # Marcar como aberto
    app.formularios_abertos[nome_formulario] = True
    
    setattr(app, editar_attr, True)
    if hasattr(form, 'FormDeducao'):
        # Para o formulário de dedução, passa app como parâmetro
        form_instance = form.FormDeducao(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    elif hasattr(form, 'FormMaterial'):
        # Para o formulário de material, passa app como parâmetro
        form_instance = form.FormMaterial(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    elif hasattr(form, 'FormEspessura'):
        # Para o formulário de espessura, passa app como parâmetro
        form_instance = form.FormEspessura(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    elif hasattr(form, 'FormCanal'):
        # Para o formulário de canal, passa app como parâmetro
        form_instance = form.FormCanal(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    elif hasattr(form, 'FormAutenticacao'):
        # Para o formulário de autenticação, passa app como parâmetro
        form_instance = form.FormAutenticacao(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    else:
        form.main(root)
        registrar_callback_fechamento(nome_formulario, root)

def form_false(form, editar_attr, root):
    '''
    Abre o formulário de criação de um item específico
    (dedução, material, espessura ou canal).
    '''
    # Determinar nome do formulário baseado no módulo
    nome_formulario = f"{form.__name__}_criacao"
    
    # Verificar se o formulário já está aberto
    if verificar_formulario_aberto(nome_formulario):
        return
    
    # Marcar como aberto
    app.formularios_abertos[nome_formulario] = True
    
    setattr(app, editar_attr, False)
    if hasattr(form, 'FormDeducao'):
        # Para o formulário de dedução, passa app como parâmetro
        form_instance = form.FormDeducao(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    elif hasattr(form, 'FormMaterial'):
        # Para o formulário de material, passa app como parâmetro
        form_instance = form.FormMaterial(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    elif hasattr(form, 'FormEspessura'):
        # Para o formulário de espessura, passa app como parâmetro
        form_instance = form.FormEspessura(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    elif hasattr(form, 'FormCanal'):
        # Para o formulário de canal, passa app como parâmetro
        form_instance = form.FormCanal(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    elif hasattr(form, 'FormAutenticacao'):
        # Para o formulário de autenticação, passa app como parâmetro
        form_instance = form.FormAutenticacao(root, app_principal=app)
        form_instance.main(root, app)
        registrar_callback_fechamento(nome_formulario, root)
    else:
        form.main(root)
        registrar_callback_fechamento(nome_formulario, root)

def carregar_interface(app_principal=None):
    '''
    Atualiza o cabeçalho e recria os widgets no frame de dobras.
    '''
    # Se não foi passada uma instância, usa a global
    if app_principal is None:
        app_principal = app
    
    # Determinar número de dobras baseado na expansão vertical
    numero_dobras = 10 if app_principal.expandir_v.get() == 1 else 5
    
    # Determinar valores de largura baseado na expansão horizontal ANTES de salvar
    novos_valores_w = [1, 2] if app_principal.expandir_h.get() == 1 else [1]
    
    # Salvar os valores dos widgets do cabeçalho se já existir um
    if hasattr(app_principal, 'cabecalho_ui') and app_principal.cabecalho_ui:
        salvar_valores_cabecalho(app_principal.cabecalho_ui)
    
    # Salvar os valores das dobras se já existirem - usar TODOS os valores_w existentes
    if hasattr(app_principal, 'dobras_ui') and app_principal.dobras_ui:
        # Salvar valores de todas as colunas existentes antes da mudança
        for w in app_principal.dobras_ui.keys():
            salvar_valores_dobra(app_principal.dobras_ui[w], w)
      # Atualizar valores_w apenas após o salvamento
    app_principal.valores_w = novos_valores_w
    
    # Limpar widgets antigos no frame superior
    for widget in app_principal.frame_superior.winfo_children():
        widget.destroy()

    # Recriar cabeçalho principal após limpeza
    app_principal.cabecalho_ui = InterfaceCabecalho(app_principal.frame_superior, None)
    app_principal.cabecalho_ui.frame.grid(row=0, column=0, sticky='ewns', ipadx=2, ipady=2)
    
    # Adicionar avisos se expansão horizontal estiver ativa
    if app_principal.expandir_h.get() == 1:
        app_principal.avisos_ui = InterfaceAvisos(app_principal.frame_superior)
        app_principal.avisos_ui.frame.grid(row=0, column=1, sticky='ewns', ipadx=2, ipady=2)

    # Criar colunas de dobras baseado nos valores_w
    app_principal.dobras_ui = {}
    for w in app_principal.valores_w:
        dobra_ui = InterfaceDobra(app_principal.cabecalho_ui, app_principal.frame_superior, w)
        dobra_ui.entradas_dobras(app_principal.cabecalho_ui, numero_dobras, w)
        dobra_ui.frame.grid(row=1, column=w-1, sticky='ewns', ipadx=2, ipady=2)
        app_principal.dobras_ui[w] = dobra_ui
    
    # Atualizar referência no cabeçalho para a primeira coluna de dobras
    if app_principal.dobras_ui:
        app_principal.cabecalho_ui.dobras_ui = app_principal.dobras_ui[1]
        app_principal.cabecalho_ui.app_principal = app_principal  # Adicionar referência para todas as colunas

    # Criar botões
    app_principal.frame_botoes = criar_botoes(app_principal.frame_superior, app_principal)
    columnspan = len(app_principal.valores_w)
    app_principal.frame_botoes.grid(row=2, column=0, sticky='ewns', ipadx=2, ipady=2, columnspan=columnspan)

    # Configurar grid weights para as colunas
    for i, w in enumerate(app_principal.valores_w):
        app_principal.frame_superior.columnconfigure(i, weight=1)    # Restaurar valores    for w in app_principal.valores_w:
        if w in app_principal.dobras_ui:
            restaurar_valores_dobra(app_principal.dobras_ui[w], w)
    
    restaurar_valores_cabecalho(app_principal.cabecalho_ui)
    
    # Chamar todas_funcoes para cada coluna de dobra criada
    for w in app_principal.valores_w:
        if w in app_principal.dobras_ui:
            todas_funcoes(app_principal.cabecalho_ui, app_principal.dobras_ui[w])

def on_closing():
    '''
    Função chamada ao fechar a janela principal.
    Salva a configuração atual antes de fechar.
    '''
    geometry = app.janela_principal.geometry()
    position = geometry.split('+')[1:]
    config = carregar_configuracao()
    config['geometry'] = f"+{position[0]}+{position[1]}"
    salvar_configuracao(config)
    app.janela_principal.destroy()

def configurar_menu(app_principal):
    '''
    Configura o menu superior da janela principal.
    '''
    menu_bar = tk.Menu(app_principal.janela_principal)
    app_principal.janela_principal.config(menu=menu_bar)

    # Menu Arquivo
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Arquivo", menu=file_menu)
    file_menu.add_command(label="Nova Dedução", command=lambda: form_false(form_deducao,
                                                                           'editar_deducao',
                                                                           app_principal.janela_principal))

    file_menu.add_command(label="Novo Material", command=lambda: form_false(form_material,
                                                                            'editar_material',
                                                                            app_principal.janela_principal))

    file_menu.add_command(label="Nova Espessura", command=lambda: form_false(form_espessura,
                                                                           'editar_espessura',
                                                                           app_principal.janela_principal))

    file_menu.add_command(label="Novo Canal", command=lambda: form_false(form_canal,
                                                                       'editar_canal',
                                                                       app_principal.janela_principal))
    file_menu.add_separator()
    file_menu.add_command(label="Sair", command=app_principal.janela_principal.destroy)
    
    # Menu Editar
    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Editar", menu=edit_menu)
    edit_menu.add_command(label="Editar Dedução", command=lambda: form_true(form_deducao,
                                                                           'editar_deducao',
                                                                           app_principal.janela_principal))

    edit_menu.add_command(label="Editar Material", command=lambda: form_true(form_material,
                                                                           'editar_material',
                                                                           app_principal.janela_principal))

    edit_menu.add_command(label="Editar Espessura", command=lambda: form_true(form_espessura,
                                                                           'editar_espessura',
                                                                           app_principal.janela_principal))

    edit_menu.add_command(label="Editar Canal", command=lambda: form_true(form_canal,
                                                                       'editar_canal',
                                                                       app_principal.janela_principal))

    # Menu Opções
    opcoes_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Opções", menu=opcoes_menu)
    app_principal.no_topo_var = tk.IntVar()
    opcoes_menu.add_checkbutton(label="No topo", variable=app_principal.no_topo_var,
                                command=lambda: no_topo(app_principal.janela_principal, app_principal))    # Menu ferramentas
    ferramentas_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ferramentas", menu=ferramentas_menu)
    ferramentas_menu.add_command(label="Razão Raio/Espessura",
                                 command=lambda: abrir_form_razao_rie(app_principal.janela_principal, app_principal))    # Menu Usuário
    usuario_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Usuário", menu=usuario_menu)
    usuario_menu.add_command(label="Login", command=lambda: abrir_form_aut(app_principal.janela_principal, app_principal, login=True))

    usuario_menu.add_command(label="Novo Usuário", command=lambda: abrir_form_aut(app_principal.janela_principal, app_principal, login=False))

    usuario_menu.add_command(label="Gerenciar Usuários",
                             command=lambda: abrir_form_usuario(app_principal.janela_principal, app_principal))
    usuario_menu.add_separator()
    usuario_menu.add_command(label="Sair", command=lambda: logout(app_principal))

    # Menu Ajuda
    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ajuda", menu=help_menu)
    help_menu.add_command(label="Sobre", command=lambda: abrir_form_sobre(app_principal.janela_principal, app_principal))

def registrar_callback_fechamento(nome_formulario, root):
    '''
    Registra callback de fechamento para remover formulário do dicionário.
    Procura pela última janela Toplevel criada e registra o callback.
    '''
    def remover_do_dicionario():
        if nome_formulario in app.formularios_abertos:
            del app.formularios_abertos[nome_formulario]
    
    # Aguardar um momento para que a janela seja criada
    def configurar_callback():
        toplevels = [widget for widget in root.winfo_children() if isinstance(widget, tk.Toplevel)]
        if toplevels:
            # Pegar a última janela Toplevel criada
            janela = toplevels[-1]
            
            # Configurar callback personalizado
            def on_close():
                remover_do_dicionario()
                try:
                    janela.destroy()
                except tk.TclError:
                    pass  # Janela já foi destruída
            
            janela.protocol("WM_DELETE_WINDOW", on_close)
    
    # Usar after para dar tempo da janela ser criada
    root.after(10, configurar_callback)

def abrir_form_sobre(root, app_principal):
    '''
    Abre o formulário "Sobre", evitando múltiplas instâncias.
    '''
    nome_formulario = "form_sobre"
    if verificar_formulario_aberto(nome_formulario):
        return
    
    # Marcar como aberto temporariamente
    app.formularios_abertos[nome_formulario] = True
    
    try:
        form_sobre.main(root, app_principal)
        # Registrar callback de fechamento
        registrar_callback_fechamento(nome_formulario, root)
    except Exception as e:
        # Se houve erro, remover do dicionário
        if nome_formulario in app.formularios_abertos:
            del app.formularios_abertos[nome_formulario]
        raise e

def abrir_form_razao_rie(root, app_principal):
    '''
    Abre o formulário "Razão Raio/Espessura", evitando múltiplas instâncias.
    '''
    nome_formulario = "form_razao_rie"
    if verificar_formulario_aberto(nome_formulario):
        return
    
    # Marcar como aberto temporariamente
    app.formularios_abertos[nome_formulario] = True
    
    try:
        form_razao_rie.main(root, app_principal)
        # Registrar callback de fechamento
        registrar_callback_fechamento(nome_formulario, root)
    except Exception as e:
        # Se houve erro, remover do dicionário
        if nome_formulario in app.formularios_abertos:
            del app.formularios_abertos[nome_formulario]
        raise e

def abrir_form_usuario(root, app_principal):
    '''
    Abre o formulário de gerenciamento de usuários, evitando múltiplas instâncias.
    '''
    nome_formulario = "form_usuario"
    if verificar_formulario_aberto(nome_formulario):
        return
    
    # Marcar como aberto temporariamente
    app.formularios_abertos[nome_formulario] = True
    
    try:
        form_usuario.main(root, app_principal)
        # Registrar callback de fechamento
        registrar_callback_fechamento(nome_formulario, root)
    except Exception as e:
        # Se houve erro, remover do dicionário
        if nome_formulario in app.formularios_abertos:
            del app.formularios_abertos[nome_formulario]
        raise e

def abrir_form_aut(root, app_principal, login=True):
    '''
    Abre o formulário de autenticação, evitando múltiplas instâncias.
    '''
    nome_formulario = f"form_aut_{'login' if login else 'registro'}"
    if verificar_formulario_aberto(nome_formulario):
        return
    
    # Marcar como aberto temporariamente
    app.formularios_abertos[nome_formulario] = True
    
    try:
        form_aut.main(root, app_principal, login=login)
        # Registrar callback de fechamento
        registrar_callback_fechamento(nome_formulario, root)
    except Exception as e:
        # Se houve erro, remover do dicionário
        if nome_formulario in app.formularios_abertos:
            del app.formularios_abertos[nome_formulario]
        raise e

def main():
    '''
    Função principal que inicializa a interface gráfica do aplicativo.
    '''
    global app
    app = InterfaceApp()
    
    # Configurar protocolo de fechamento da janela
    app.janela_principal.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Configurar menu - passar a instância como parâmetro
    configurar_menu(app)
    
    # Carregar interface inicial
    carregar_interface()
    
    # Verificar se existe admin
    verificar_admin_existente(app)
    
    # Iniciar loop principal
    app.janela_principal.mainloop()

if __name__ == "__main__":
    main()
