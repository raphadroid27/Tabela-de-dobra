import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
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

CONFIG_FILE = 'config.json'

def carregar_configuracao():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def salvar_configuracao(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def main():
    config = carregar_configuracao()
    root = tk.Tk()
    root.title("Cálculo de Dobra")
    root.geometry(config.get('geometry'))  # Usando a configuração carregada ou um valor padrão
    root.resizable(False, False)

    root.update_idletasks() 
    print(f"{root.winfo_width()}x{root.winfo_height()}")

    def set_topmost(window, on_top):
        if window and window.winfo_exists():
            window.attributes("-topmost",on_top)

    def on_top():
        on_top_valor = g.on_top_var.get() == 1
        root.attributes("-topmost", on_top_valor)
        set_topmost(g.deducao_form, on_top_valor)
        set_topmost(g.material_form, on_top_valor)
        set_topmost(g.canal_form, on_top_valor)
        set_topmost(g.espessura_form, on_top_valor)

    def editar_deducao_form(root):
        g.editar_deducao = True 
        form_deducao.main(root)
               
    def add_deducao_form(root):
        g.editar_deducao = False
        form_deducao.main(root)
        
    def editar_material_form(root):
        g.editar_material = True
        form_material.main(root)

    def add_material_form(root):
        g.editar_material = False
        form_material.main(root)

    def editar_canal_form(root):
        g.editar_canal = True
        form_canal.main(root)

    def add_canal_form(root):
        g.editar_canal = False
        form_canal.main(root)

    def editar_espessura_form(root):
        g.editar_espessura = True
        form_espessura.main(root)

    def add_espessura_form(root):
        g.editar_espessura = False
        form_espessura.main(root)  

    def on_closing():
        config['geometry'] = root.geometry()
        salvar_configuracao(config)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Criando o menu superior
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)

    # Adicionando menus
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Arquivo", menu=file_menu)
    file_menu.add_command(label="Nova Dedução", command=lambda: add_deducao_form(root))
    file_menu.add_command(label="Novo Material", command=lambda: add_material_form(root))
    file_menu.add_command(label="Nova Espessura", command=lambda: add_espessura_form(root))
    file_menu.add_command(label="Novo Canal", command=lambda: add_canal_form(root))
    file_menu.add_separator()
    file_menu.add_command(label="Sair", command=on_closing)

    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Editar", menu=edit_menu)
    edit_menu.add_command(label="Editar Dedução", command=lambda: editar_deducao_form(root))
    edit_menu.add_command(label="Editar Material", command=lambda: editar_material_form(root))
    edit_menu.add_command(label="Editar Espessura", command=lambda: editar_espessura_form(root))
    edit_menu.add_command(label="Editar Canal", command=lambda: editar_canal_form(root))

    opcoes_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Opções", menu=opcoes_menu)
    g.on_top_var = tk.IntVar()
    opcoes_menu.add_checkbutton(label="No topo", variable=g.on_top_var, command=on_top)

    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ajuda", menu=help_menu)
    help_menu.add_command(label="Sobre", command=lambda:form_sobre.main(root))

    cabecalho(root)

    # Criando o Notebook (abas)
    notebook = ttk.Notebook(root, height=140)
    notebook.pack(fill='both', expand=True, padx=10, pady=5)

    criar_aba1(notebook)
    #criar_aba2(notebook)
    criar_aba3(notebook)

    frame_botoes = tk.Frame(root, width=200)
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

    # Funções de copiar
    g.deducao_label.bind("<Button-1>", lambda event: copiar_deducao())
    g.fator_k_label.bind("<Button-1>", lambda event: copiar_fatork())
    g.offset_label.bind("<Button-1>", lambda event: copiar_offset())
    g.medida_blank_label.bind("<Button-1>", lambda event: copiar_blank())
    g.metade_blank_label.bind("<Button-1>", lambda event: copiar_metade_blank())

    for i in range(1, 6):
        getattr(g, f'medidadobra{i}_label').bind("<Button-1>", lambda event, i=i: copiar_medidadobra(i))
        getattr(g, f'metadedobra{i}_label').bind("<Button-1>", lambda event, i=i: copiar_metadedobra(i))
    
    root.mainloop()

if __name__ == "__main__":
    main()