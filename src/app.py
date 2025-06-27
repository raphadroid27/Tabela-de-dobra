"""
# Formulário Principal do Aplicativo de Cálculo de Dobra
# Este módulo implementa a interface principal do aplicativo, permitindo a
# gestão de deduções, materiais, espessuras e canais. Ele utiliza a biblioteca
# tkinter para a interface gráfica, o módulo globals para variáveis globais,
# e outros módulos auxiliares para operações relacionadas ao banco de dados
# e funcionalidades específicas.
"""

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
from src.config import globals as g
from src.utils.janelas import no_topo
from src.utils.interface_manager import carregar_interface

# Definir a função globalmente para evitar importação cíclica
g.CARREGAR_INTERFACE_FUNC = carregar_interface
from src.utils.utilitarios import obter_caminho_icone
from src.utils.usuarios import logout
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

def configurar_janela_principal(config):
    """
    Configura a janela principal do aplicativo.
    """
    g.PRINC_FORM = tk.Tk()
    g.PRINC_FORM.title("Cálculo de Dobra")
    g.PRINC_FORM.geometry('340x400')
    if 'geometry' in config:
        g.PRINC_FORM.geometry(config['geometry'])
    g.PRINC_FORM.resizable(False, False)
    g.PRINC_FORM.update_idletasks()

    icone_path = obter_caminho_icone()
    g.PRINC_FORM.iconbitmap(icone_path)

    def on_closing():
        if g.PRINC_FORM is not None:
            geometry = g.PRINC_FORM.geometry()
            position = geometry.split('+')[1:]
            config['geometry'] = f"+{position[0]}+{position[1]}"
            salvar_configuracao(config)
            g.PRINC_FORM.destroy()

    g.PRINC_FORM.protocol("WM_DELETE_WINDOW", on_closing)

def configurar_menu():
    """
    Configura o menu superior da janela principal.
    """
    if g.PRINC_FORM is None:
        return

    menu_bar = tk.Menu(g.PRINC_FORM)
    g.PRINC_FORM.config(menu=menu_bar)    # Menu Arquivo
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Arquivo", menu=file_menu)

    file_menu.add_command(label="Nova Dedução", command=lambda: form_false(form_deducao,
                                                                           'EDIT_DED',
                                                                           g.PRINC_FORM))

    file_menu.add_command(label="Novo Material", command=lambda: form_false(form_material,
                                                                            'EDIT_MAT',
                                                                            g.PRINC_FORM))

    file_menu.add_command(label="Nova Espessura", command=lambda: form_false(form_espessura,
                                                                           'EDIT_ESP',
                                                                           g.PRINC_FORM))

    file_menu.add_command(label="Novo Canal", command=lambda: form_false(form_canal,
                                                                       'EDIT_CANAL',
                                                                       g.PRINC_FORM))
    file_menu.add_separator()
    file_menu.add_command(label="Sair",
                          command=lambda: g.PRINC_FORM.destroy() if g.PRINC_FORM else None)

    # Menu Editar
    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Editar", menu=edit_menu)
    edit_menu.add_command(label="Editar Dedução", command=lambda: form_true(form_deducao,
                                                                           'EDIT_DED',
                                                                           g.PRINC_FORM))

    edit_menu.add_command(label="Editar Material", command=lambda: form_true(form_material,
                                                                           'EDIT_MAT',
                                                                           g.PRINC_FORM))

    edit_menu.add_command(label="Editar Espessura", command=lambda: form_true(form_espessura,
                                                                           'EDIT_ESP',
                                                                           g.PRINC_FORM))

    edit_menu.add_command(label="Editar Canal", command=lambda: form_true(form_canal,
                                                                       'EDIT_CANAL',
                                                                       g.PRINC_FORM))

    # Menu Opções
    opcoes_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Opções", menu=opcoes_menu)
    g.NO_TOPO_VAR = tk.IntVar()
    opcoes_menu.add_checkbutton(label="No topo", variable=g.NO_TOPO_VAR,
                                command=lambda: no_topo(g.PRINC_FORM))


    # Menu ferramentas
    ferramentas_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ferramentas", menu=ferramentas_menu)
    ferramentas_menu.add_command(label="Razão Raio/Espessura",
                                 command=lambda: form_razao_rie.main(g.PRINC_FORM))

    # Menu Usuário
    usuario_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Usuário", menu=usuario_menu)
    usuario_menu.add_command(label="Login", command=lambda: form_true(form_aut,
                                                                      "LOGIN",
                                                                      g.PRINC_FORM))

    usuario_menu.add_command(label="Novo Usuário", command=lambda: form_false(form_aut,
                                                                           "LOGIN",
                                                                           g.PRINC_FORM))

    usuario_menu.add_command(label="Gerenciar Usuários",
                             command=lambda: form_usuario.main(g.PRINC_FORM))
    usuario_menu.add_separator()
    usuario_menu.add_command(label="Sair", command=logout)

    # Menu Ajuda
    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ajuda", menu=help_menu)
    help_menu.add_command(label="Sobre", command=lambda: form_sobre.main(g.PRINC_FORM))


def configurar_frames():
    """
    Configura os frames principais da janela.
    """
    frame_superior = tk.LabelFrame(g.PRINC_FORM)
    frame_superior.pack(fill='both', expand=True, padx=10, pady=10)

    frame_superior.columnconfigure(0, weight=1)
    frame_superior.columnconfigure(1, weight=1)
    frame_superior.rowconfigure(0, weight=1)
    frame_superior.rowconfigure(1, weight=1)

    g.VALORES_W = [1]
    g.EXP_V = tk.IntVar()
    g.EXP_H = tk.IntVar()
    carregar_interface(1, frame_superior)


def main():
    """
    Função principal que inicializa a interface gráfica do aplicativo.
    """
    config = carregar_configuracao()
    configurar_janela_principal(config)
    configurar_menu()
    configurar_frames()
    verificar_admin_existente()
    if g.PRINC_FORM is not None:
        g.PRINC_FORM.mainloop()

if __name__ == "__main__":
    main()
