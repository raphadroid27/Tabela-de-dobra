import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import globals as g
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def cabecalho(root):
    cabecalho = ttk.Frame(root)
    cabecalho.pack(padx=10, fill='both', expand=True)

    # Primeira linha frame
    main_frame = tk.Frame(cabecalho)
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
    g.material_combobox = ttk.Combobox(main_frame, width=10,justify="center")
    g.material_combobox.grid(row=1, column=0, padx=2, sticky='we')
    g.material_combobox.bind("<<ComboboxSelected>>", func=lambda event: [todas_funcoes(w) for w in g.valores_w])

    tk.Label(main_frame, text="Espessura:").grid(row=0, column=1, sticky='sw')
    g.espessura_combobox = ttk.Combobox(main_frame, width=10,justify="center")
    g.espessura_combobox.grid(row=1, column=1, padx=2, sticky='we')
    g.espessura_combobox.bind("<<ComboboxSelected>>", func=lambda event: [todas_funcoes(w) for w in g.valores_w])

    tk.Label(main_frame, text="Canal:").grid(row=0, column=2, sticky='sw')
    g.canal_combobox = ttk.Combobox(main_frame, width=10,justify="center")
    g.canal_combobox.grid(row=1, column=2, padx=2, sticky='we')
    g.canal_combobox.bind("<<ComboboxSelected>>", func=lambda event: [todas_funcoes(w) for w in g.valores_w])

    tk.Label(main_frame, text="Comprimento:").grid(row=0, column=3, sticky='sw')
    g.comprimento_entry = tk.Entry(main_frame, width=10, justify="center")
    g.comprimento_entry.grid(row=1, column=3, padx=2, sticky='we')
    g.comprimento_entry.bind("<KeyRelease>", func=lambda event: atualizar_toneladas_m())


    # Raio interno
    tk.Label(main_frame, text="Raio Int.:").grid(row=2, column=0, sticky='sw')
    g.raio_interno_entry = tk.Entry(main_frame, width=10, justify="center")
    g.raio_interno_entry.grid(row=3, column=0, padx=2, sticky='we')
    g.raio_interno_entry.bind("<KeyRelease>", func=lambda event: [todas_funcoes(w) for w in g.valores_w])

    # Fator K
    tk.Label(main_frame, text="Fator K:").grid(row=2, column=1, sticky='sw')
    g.fator_k_label = tk.Label(main_frame, relief="sunken", width=10)
    g.fator_k_label.grid(row=3, column=1, padx=2, sticky='we')
    g.fator_k_label.bind("<Button-1>", func=lambda event: copiar('fator_k'))

    # Dedução
    tk.Label(main_frame, text="Dedução:").grid(row=2, column=2, sticky='sw')
    g.deducao_label = tk.Label(main_frame, relief="sunken", width=10)
    g.deducao_label.grid(row=3, column=2, padx=2, sticky='we')
    g.deducao_label.bind("<Button-1>", func=lambda event: copiar('deducao'))

    # Offset
    tk.Label(main_frame, text="Offset:").grid(row=2, column=3, sticky='sw')
    g.offset_label = tk.Label(main_frame, relief="sunken", width=10)
    g.offset_label.grid(row=3, column=3, padx=2, sticky='we')
    g.offset_label.bind("<Button-1>", func=lambda event: copiar('offset'))

    # Dedução específica
    tk.Label(main_frame, text="Ded. Espec.:").grid(row=4, column=0, sticky='sw')
    g.deducao_espec_entry = tk.Entry(main_frame, width=10, fg="red", justify="center")
    g.deducao_espec_entry.grid(row=5, column=0, padx=2, sticky='we')

    # Aba mínima
    tk.Label(main_frame, text="Aba Mín.:").grid(row=4, column=1, sticky='sw')
    g.aba_min_externa_label = tk.Label(main_frame, relief="sunken", width=10)
    g.aba_min_externa_label.grid(row=5, column=1, padx=2, sticky='we')

    # Z90°
    tk.Label(main_frame, text="Mín. Ext. Z90°:").grid(row=4, column=2, sticky='sw')
    g.z_min_externa_label = tk.Label(main_frame, relief="sunken", width=10)
    g.z_min_externa_label.grid(row=5, column=2, padx=2, sticky='we')

    # tom/m
    tk.Label(main_frame, text="Ton/m:").grid(row=4, column=3, sticky='sw')
    g.ton_m_label = tk.Label(main_frame, relief="sunken", width=10)
    g.ton_m_label.grid(row=5, column=3, padx=2, sticky='we')

    #Observações
    g.obs_label = tk.Label(main_frame, text="Observações:", relief="sunken", anchor='w')
    g.obs_label.grid(row=6, column=0, columnspan=4, sticky='wen', padx=2, pady=5)

    atualizar_material()