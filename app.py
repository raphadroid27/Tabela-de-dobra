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
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True)

    criar_aba1(notebook)
    criar_aba2(notebook)
    criar_aba3(notebook)
    
    root.mainloop()

if __name__ == "__main__":
    main()