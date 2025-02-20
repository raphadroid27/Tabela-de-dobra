import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao, usuario
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import json
import os
from aba_dobra_90 import criar_aba1
from aba2 import criar_aba2
from aba_raio_fatorK import criar_aba3
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
    g.principal_form.geometry(config.get('geometry'))
    g.principal_form.resizable(False, False)

    g.principal_form.update_idletasks() 

    def on_closing():
        config['geometry'] = g.principal_form.geometry()
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
    opcoes_menu.add_checkbutton(label="No topo", variable=g.on_top_var, command=lambda: on_top(g.principal_form))

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

    # Criando o Notebook (abas)
    notebook = ttk.Notebook(g.principal_form, height=140)
    notebook.pack(fill='both', expand=True, padx=10, pady=5)

    criar_aba1(notebook)
    # criar_aba2(notebook)
    criar_aba3(notebook)

    frame_botoes = tk.Frame(g.principal_form, width=200)
    frame_botoes.pack(expand=True)

    frame_botoes.columnconfigure(0, weight=1)
    frame_botoes.columnconfigure(1, weight=1)

    # Botão para limpar valores de dobras
    limpar_dobras_button = tk.Button(frame_botoes, text="Limpar Dobras", command=limpar_dobras, width=15, bg='yellow')
    limpar_dobras_button.grid(row=0, column=0, sticky='we', padx=2)

    # Botão para limpar todos os valores
    limpar_tudo_button = tk.Button(frame_botoes, text="Limpar Tudo", command=limpar_tudo, width=15, bg='red')
    limpar_tudo_button.grid(row=0, column=1, sticky='we', padx=2)

    # Funções de atualização
    entries = [
        g.deducao_label, g.deducao_espec_entry, g.aba1_entry, g.aba2_entry, 
        g.aba3_entry, g.aba4_entry, g.aba5_entry, g.raio_interno_entry, g.comprimento_entry
    ]
    comboboxes = [g.canal_combobox, g.espessura_combobox, g.material_combobox]

    for entry in entries:
        entry.bind("<KeyRelease>", lambda event: todas_funcoes())

    for combobox in comboboxes:
        combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())

    for i in range(1, 6):
        getattr(g, f'medidadobra{i}_label').bind("<Button-1>", lambda event, i=i: copiar_medidadobra(i))
        getattr(g, f'metadedobra{i}_label').bind("<Button-1>", lambda event, i=i: copiar_metadedobra(i))
    
    verificar_admin_existente()
    g.principal_form.mainloop()

if __name__ == "__main__":
    main()