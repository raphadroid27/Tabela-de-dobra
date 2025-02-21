import tkinter as tk
from tkinter import ttk, messagebox
from models import deducao, espessura, material, canal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import globals as g
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):
    # Verificar se a janela já está aberta
    if g.deducao_form is not None:
        g.deducao_form.destroy()   
        pass
    
    g.deducao_form = tk.Toplevel()
    g.deducao_form.geometry("500x420")
    g.deducao_form.resizable(False, False)

    no_topo(g.deducao_form)
    posicionar_janela(g.deducao_form, 'direita')
    
    main_frame = tk.Frame(g.deducao_form)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)

    main_frame.rowconfigure(0, weight=0)
    main_frame.rowconfigure(1, weight=1)
    main_frame.rowconfigure(2, weight=0)
    main_frame.rowconfigure(3, weight=0)

    frame_busca = tk.LabelFrame(main_frame, text='Buscar Deduções', pady=5)
    frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    frame_busca.columnconfigure(0, weight=1)
    frame_busca.columnconfigure(1, weight=1)
    frame_busca.columnconfigure(2, weight=1)
    frame_busca.columnconfigure(3, weight=0)

    tk.Label(frame_busca, text="Material:").grid(row=0, column=0, padx=2, sticky='sw')
    g.deducao_material_combobox = ttk.Combobox(frame_busca)
    g.deducao_material_combobox.grid(row=1, column=0, padx=5, sticky="ew")
    g.deducao_material_combobox.bind("<<ComboboxSelected>>", lambda event: buscar('dedução'))

    tk.Label(frame_busca, text="Espessura:").grid(row=0, column=1, padx=2, sticky='sw')
    g.deducao_espessura_combobox = ttk.Combobox(frame_busca)
    g.deducao_espessura_combobox.grid(row=1, column=1, padx=5, sticky="ew")
    g.deducao_espessura_combobox.bind("<<ComboboxSelected>>", lambda event: buscar('dedução'))

    tk.Label(frame_busca, text="Canal:").grid(row=0, column=2, padx=2, sticky='sw')
    g.deducao_canal_combobox = ttk.Combobox(frame_busca)
    g.deducao_canal_combobox.grid(row=1, column=2, padx=5, sticky="ew")
    g.deducao_canal_combobox.bind("<<ComboboxSelected>>", lambda event: buscar('dedução'))

    tk.Button(frame_busca, text="Limpar", command = lambda: limpar_busca('dedução')).grid(row=1, column=3, padx=5, pady=5)

    columns = ("Id","Material", "Espessura","Canal", "Dedução", "Observação", "Força")
    g.lista_deducao = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        g.lista_deducao["displaycolumns"] = ("Material", "Espessura", "Canal", "Dedução", "Observação", "Força")
        g.lista_deducao.heading(col, text=col)
        g.lista_deducao.column(col, anchor="center", width=60)
        g.lista_deducao.column("Material", width=80)
        g.lista_deducao.column("Observação", width=120, anchor="w")

    g.lista_deducao.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    listar('dedução')

    frame_edicoes = tk.LabelFrame(main_frame, pady=5)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    frame_edicoes.columnconfigure(0, weight=2)
    frame_edicoes.columnconfigure(1, weight=2)
    frame_edicoes.columnconfigure(2, weight=2)
    frame_edicoes.columnconfigure(3, weight=1)

    tk.Label(frame_edicoes, text="Dedução:").grid(row=0, column=0, padx=2, sticky='sw')
    g.deducao_valor_entry = tk.Entry(frame_edicoes)
    g.deducao_valor_entry.grid(row=1, column=0, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Observação:").grid(row=0, column=1,padx=2, sticky='sw')
    g.deducao_obs_entry = tk.Entry(frame_edicoes)
    g.deducao_obs_entry.grid(row=1, column=1, padx=5, sticky="ew")

    tk.Label(frame_edicoes, text="Força:").grid(row=0, padx=2, column=2, sticky='sw')
    g.deducao_forca_entry = tk.Entry(frame_edicoes)
    g.deducao_forca_entry.grid(row=1, column=2, padx=5, sticky="ew")


    if g.editar_deducao == True:
        g.deducao_form.title("Editar/Excluir Dedução")
        frame_edicoes.config(text='Editar Dedução')
        tk.Button(frame_edicoes, text="Atualizar", command = lambda: atualizar('dedução'), bg="green").grid(row=1, column=3, padx=5, pady=5, sticky="eW")       
        tk.Button(main_frame, text="Excluir", command = lambda: excluir('dedução'), bg="red").grid(row=2, column=0, padx=5, pady=5,sticky="e")
    else:
        g.deducao_form.title("Adicionar Dedução")
        frame_edicoes.config(text='Nova Dedução')
        tk.Button(frame_edicoes, text="Adicionar", command = lambda: adicionar('dedução'), bg="cyan").grid(row=1, column=3, padx=5, pady=5, sticky="eW")

    atualizar_combobox_deducao()
          
    g.deducao_form.mainloop()

if __name__ == "__main__":
    main(None)