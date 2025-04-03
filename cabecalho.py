import tkinter as tk
from tkinter import ttk
from models import Canal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import globals as g
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def cabecalho(root):
    frame_cabecalho = ttk.Frame(root)
    frame_cabecalho.grid(row=0, column=0, sticky='nsew', padx=10)

    main_frame = tk.Frame(frame_cabecalho)
    main_frame.pack(fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.columnconfigure(2, weight=1)
    main_frame.columnconfigure(3, weight=1)

    main_frame.rowconfigure(0, weight=0)
    main_frame.rowconfigure(1, weight=0)
    main_frame.rowconfigure(2, weight=0)
    main_frame.rowconfigure(3, weight=0)
    main_frame.rowconfigure(4, weight=0)
    main_frame.rowconfigure(5, weight=0)
    main_frame.rowconfigure(6, weight=0)

    tk.Label(main_frame, text="Material:").grid(row=0, column=0, sticky='sw')
    g.MAT_COMB = ttk.Combobox(main_frame, width=10,justify="center")
    g.MAT_COMB.grid(row=1, column=0, padx=2, sticky='we')
    g.MAT_COMB.bind("<<ComboboxSelected>>", func=lambda event: [todas_funcoes(w) for w in g.VALORES_W])
    tp.ToolTip(g.MAT_COMB, "Selecione o material")

    tk.Label(main_frame, text="Espessura:").grid(row=0, column=1, sticky='sw')
    g.ESP_COMB = ttk.Combobox(main_frame, width=10,justify="center")
    g.ESP_COMB.grid(row=1, column=1, padx=2, sticky='we')
    g.ESP_COMB.bind("<<ComboboxSelected>>", func=lambda event: [todas_funcoes(w) for w in g.VALORES_W])
    tp.ToolTip(g.ESP_COMB, "Selecione a espessura da peça.")

    tk.Label(main_frame, text="Canal:").grid(row=0, column=2, sticky='sw')
    g.CANAL_COMB = ttk.Combobox(main_frame, width=10,justify="center")
    g.CANAL_COMB.grid(row=1, column=2, padx=2, sticky='we')
    g.CANAL_COMB.bind("<<ComboboxSelected>>", func=lambda event: [todas_funcoes(w) for w in g.VALORES_W])
    tp.ToolTip(g.CANAL_COMB, "Selecione o canal de dobra.")

    tk.Label(main_frame, text="Comprimento:").grid(row=0, column=3, sticky='sw')
    g.COMPR_ENTRY = tk.Entry(main_frame, width=10, justify="center")
    g.COMPR_ENTRY.grid(row=1, column=3, padx=2, sticky='we')
    g.COMPR_ENTRY.bind("<KeyRelease>", func=lambda event: atualizar_toneladas_m())
    tp.ToolTip(g.COMPR_ENTRY, "Digite o comprimento da peça em milímetros.")

    # Raio interno
    tk.Label(main_frame, text="Raio Int.:").grid(row=2, column=0, sticky='sw')
    g.RI_ENTRY = tk.Entry(main_frame, width=10, justify="center")
    g.RI_ENTRY.grid(row=3, column=0, padx=2, sticky='we')
    g.RI_ENTRY.bind("<KeyRelease>", func=lambda event: [todas_funcoes(w) for w in g.VALORES_W])
    tp.ToolTip(g.RI_ENTRY, "Digite o raio interno da peça em milímetros.")

    # Fator K
    tk.Label(main_frame, text="Fator K:").grid(row=2, column=1, sticky='sw')
    g.K_LBL = tk.Label(main_frame, relief="sunken", width=10)
    g.K_LBL.grid(row=3, column=1, padx=2, sticky='we')
    g.K_LBL.bind("<Button-1>", func=lambda event: copiar('fator_k'))

    # Dedução
    tk.Label(main_frame, text="Dedução:").grid(row=2, column=2, sticky='sw')
    g.DED_COMB = tk.Label(main_frame, relief="sunken", width=10)
    g.DED_COMB.grid(row=3, column=2, padx=2, sticky='we')
    g.DED_COMB.bind("<Button-1>", func=lambda event: copiar('dedução'))

    # Offset
    tk.Label(main_frame, text="Offset:").grid(row=2, column=3, sticky='sw')
    g.OFFSET_LBL = tk.Label(main_frame, relief="sunken", width=10)
    g.OFFSET_LBL.grid(row=3, column=3, padx=2, sticky='we')
    g.OFFSET_LBL.bind("<Button-1>", func=lambda event: copiar('offset'))

    # Dedução específica
    tk.Label(main_frame, text="Ded. Espec.:").grid(row=4, column=0, sticky='sw')
    g.DED_ESPEC_ENTRY = tk.Entry(main_frame, width=10, fg="blue", justify="center")
    g.DED_ESPEC_ENTRY.grid(row=5, column=0, padx=2, sticky='we')
    g.DED_ESPEC_ENTRY.bind("<KeyRelease>", func=lambda event: [todas_funcoes(w) for w in g.VALORES_W])
    tp.ToolTip(g.DED_ESPEC_ENTRY, "Digite a dedução específica da peça em milímetros.")

    # Aba mínima
    tk.Label(main_frame, text="Aba Mín.:").grid(row=4, column=1, sticky='sw')
    g.ABA_EXT_LBL = tk.Label(main_frame, relief="sunken", width=10)
    g.ABA_EXT_LBL.grid(row=5, column=1, padx=2, sticky='we')

    # Z90°
    tk.Label(main_frame, text="Mín. Ext. Z90°:").grid(row=4, column=2, sticky='sw')
    g.Z_EXT_LBL = tk.Label(main_frame, relief="sunken", width=10)
    g.Z_EXT_LBL.grid(row=5, column=2, padx=2, sticky='we')

    # tom/m
    tk.Label(main_frame, text="Ton/m:").grid(row=4, column=3, sticky='sw')
    g.FORCA_LBL = tk.Label(main_frame, relief="sunken", width=10)
    g.FORCA_LBL.grid(row=5, column=3, padx=2, sticky='we')

    #Observações
    g.OBS_LBL = tk.Label(main_frame, text="Observações:", relief="sunken", anchor='w')
    g.OBS_LBL.grid(row=6, column=0, columnspan=4, sticky='wen', padx=2, pady=5)

    atualizar_material()

    return frame_cabecalho