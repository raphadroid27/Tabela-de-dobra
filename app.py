import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import json
import os
from aba1 import criar_aba1
from aba2 import criar_aba2
from aba3 import criar_aba3
from head import cabecalho
import add_form
import globals as g
from funcoes import *

CONFIG_FILE = 'config.json'

def carregar_configuracao():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def salvar_configuracao(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def abrir_add_form(root):
    add_form.main(root)  # Passando a janela principal para o add_form

def main():
    config = carregar_configuracao()
    root = tk.Tk()
    root.title("Tabela de dobra")
    root.geometry(config.get('geometry'))  # Usando a configuração carregada ou um valor padrão
    root.resizable(False, False)

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
    file_menu.add_command(label="Nova dedução", command=lambda: abrir_add_form(root))  # Passando a janela principal
    file_menu.add_separator()
    file_menu.add_command(label="Sair", command=on_closing)

    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Editar", menu=edit_menu)
    edit_menu.add_command(label="Desfazer")
    edit_menu.add_command(label="Refazer")

    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ajuda", menu=help_menu)
    help_menu.add_command(label="Sobre")

    cabecalho(root)

    # Criando o Notebook (abas)
    notebook = ttk.Notebook(root, height=200)
    notebook.pack(fill='both', expand=True, padx=15)

    criar_aba1(notebook)
    criar_aba2(notebook)
    criar_aba3(notebook)

    # Botão para limpar todos os valores
    limpar_tudo_button = tk.Button(root, text="Limpar Tudo", command=limpar_tudo, width=15, bg='red')
    limpar_tudo_button.pack(pady=5)

    # Funções de atualização
    entries = [
        g.deducao_entry, g.deducao_espec_entry, g.aba1_entry, g.aba2_entry, 
        g.aba3_entry, g.aba4_entry, g.aba5_entry, g.raio_interno_entry
    ]
    comboboxes = [g.canal_combobox, g.espessura_combobox, g.material_combobox]

    for entry in entries:
        entry.bind("<KeyRelease>", lambda event: todas_funcoes())

    for combobox in comboboxes:
        combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())

    # Funções de copiar
    g.deducao_entry.bind("<Button-1>", lambda event: copiar_deducao())
    g.fator_k_entry.bind("<Button-1>", lambda event: copiar_fatork())
    g.offset_entry.bind("<Button-1>", lambda event: copiar_offset())
    g.medida_blank_label.bind("<Button-1>", lambda event: copiar_blank())

    for i in range(1, 6):
        getattr(g, f'medidadobra{i}_entry').bind("<Button-1>", lambda event, i=i: copiar_medidadobra(i))
        getattr(g, f'metadedobra{i}_entry').bind("<Button-1>", lambda event, i=i: copiar_metadedobra(i))

    root.mainloop()

if __name__ == "__main__":
    main()