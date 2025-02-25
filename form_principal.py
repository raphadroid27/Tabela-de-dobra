import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao, usuario
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import json
import os
from dobra_90 import dados_dobra
from cabecalho import cabecalho
import form_espessura
import globals as g
from funcoes import *
import form_deducao
import form_material
import form_canal
import form_sobre 
import form_aut
import form_usuario

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

CONFIG_FILE = 'config.json'

def verificar_admin_existente():
    admin_existente = session.query(usuario).filter(usuario.admin == 1).first()
    if not admin_existente:
        form_aut.main(g.principal_form)

def carregar_configuracao():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def salvar_configuracao(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def form_true(form, editar_attr, root):
    setattr(g, editar_attr, True)
    form.main(root)

def form_false(form, editar_attr, root):
    setattr(g, editar_attr, False)
    form.main(root)

def main():
    config = carregar_configuracao()
    g.principal_form = tk.Tk()
    g.principal_form.title("Cálculo de Dobra")
    g.principal_form.geometry('340x400')
    if 'geometry' in config:
        g.principal_form.geometry(config['geometry'])
    g.principal_form.resizable(False, False)
    g.principal_form.update_idletasks() 

    def on_closing():
        geometry = g.principal_form.geometry()
        # Extrair apenas a posição da string de geometria
        position = geometry.split('+')[1:]
        config['geometry'] = f"+{position[0]}+{position[1]}"
        salvar_configuracao(config)
        g.principal_form.destroy()

    g.principal_form.protocol("WM_DELETE_WINDOW", on_closing)  

    # Criando o menu superior
    menu_bar = tk.Menu(g.principal_form)
    g.principal_form.config(menu=menu_bar)

    # Adicionando menus
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Arquivo", menu=file_menu)
    file_menu.add_command(label="Nova Dedução", command=lambda: form_false(form_deducao, 'editar_deducao', g.principal_form))
    file_menu.add_command(label="Novo Material", command=lambda: form_false(form_material, 'editar_material', g.principal_form))
    file_menu.add_command(label="Nova Espessura", command=lambda: form_false(form_espessura, 'editar_espessura', g.principal_form))
    file_menu.add_command(label="Novo Canal", command=lambda: form_false(form_canal, 'editar_canal', g.principal_form))
    file_menu.add_separator()
    file_menu.add_command(label="Sair", command=on_closing)

    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Editar", menu=edit_menu)
    edit_menu.add_command(label="Editar Dedução", command=lambda: form_true(form_deducao, 'editar_deducao', g.principal_form))
    edit_menu.add_command(label="Editar Material", command=lambda: form_true(form_material, 'editar_material', g.principal_form))
    edit_menu.add_command(label="Editar Espessura", command=lambda: form_true(form_espessura, 'editar_espessura', g.principal_form))
    edit_menu.add_command(label="Editar Canal", command=lambda: form_true(form_canal, 'editar_canal', g.principal_form))

    opcoes_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Opções", menu=opcoes_menu)
    g.on_top_var = tk.IntVar()
    opcoes_menu.add_checkbutton(label="No topo", variable=g.on_top_var, command=lambda: no_topo(g.principal_form))

    usuario_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Usuário", menu=usuario_menu)
    usuario_menu.add_command(label="Login", command=lambda: form_true(form_aut,"login",g.aut_form))
    usuario_menu.add_command(label="Novo Usuário", command=lambda: form_false(form_aut,"login",g.aut_form))
    usuario_menu.add_command(label="Gerenciar Usuários", command=lambda: form_usuario.main(g.principal_form))
    usuario_menu.add_separator()
    usuario_menu.add_command(label="Sair", command=logout)

    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ajuda", menu=help_menu)
    help_menu.add_command(label="Sobre", command=lambda: form_sobre.main(g.principal_form))

    cabecalho(g.principal_form)
    dados_dobra(g.principal_form)

    frame_botoes = tk.Frame(g.principal_form, width=200)
    frame_botoes.pack(expand=True)

    frame_botoes.columnconfigure(0, weight=1)
    frame_botoes.columnconfigure(1, weight=1)

    # Botão para limpar valores de dobras
    tk.Button(frame_botoes, text="Limpar Dobras", command=limpar_dobras, width=15, bg='yellow').grid(row=0, column=0, sticky='we', padx=2)

    # Botão para limpar todos os valores
    tk.Button(frame_botoes, text="Limpar Tudo", command=limpar_tudo, width=15, bg='red').grid(row=0, column=1, sticky='we', padx=2)
     
    verificar_admin_existente()
    g.principal_form.mainloop()

if __name__ == "__main__":
    main()