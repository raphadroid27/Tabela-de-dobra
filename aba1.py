import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from head import *
import head as h

def criar_aba1(notebook):

    global material_combobox, espessura_combobox, canal_combobox, deducao_entry, raio_interno_valor, fator_k_entry

    # Funções

    def calcular_dobra():
        if deducao_entry.get() == "":
            print('Dedução não informada')
            return
        else:
            deducao_valor = float(deducao_entry.get())
            print(deducao_valor)

            # Calculo da medida da linha de dobra 1
            if dobra1.get() == "":
                atualizar_medida(medidadobra1_entry, "")
                atualizar_medida(metadedobra1_entry, "")
                return
            else:
                medidadobra1 = float(dobra1.get()) - (deducao_valor / 2)
                atualizar_medida(medidadobra1_entry, medidadobra1)

            # Calculo da medida da linha de dobra 2
            if dobra2.get() == "":
                atualizar_medida(medidadobra2_entry, "")
                atualizar_medida(metadedobra2_entry, "")
                return
            else:
                if dobra3.get() == "":
                    medidadobra2 = float(dobra2.get()) - (deducao_valor / 2)
                else:
                    medidadobra2 = float(dobra2.get()) - deducao_valor
                atualizar_medida(medidadobra2_entry, medidadobra2)

            # Calculo da medida da linha de dobra 3
            if dobra3.get() == "":
                atualizar_medida(medidadobra3_entry, "")
                atualizar_medida(metadedobra3_entry, "")
                return
            else:
                if dobra4.get() == "":
                    medidadobra3 = float(dobra3.get()) - (deducao_valor / 2)
                else:
                    medidadobra3 = float(dobra3.get()) - deducao_valor
                atualizar_medida(medidadobra3_entry, medidadobra3)

            # Calculo da medida da linha de dobra 4
            if dobra4.get() == "":
                atualizar_medida(medidadobra4_entry, "")
                atualizar_medida(metadedobra4_entry, "")
                return
            else:
                if dobra5.get() == "":
                    medidadobra4 = float(dobra4.get()) - (deducao_valor / 2)
                else:
                    medidadobra4 = float(dobra4.get()) - deducao_valor
                atualizar_medida(medidadobra4_entry, medidadobra4)

            # Calculo da medida da linha de dobra 5
            if dobra5.get() == "":
                atualizar_medida(medidadobra5_entry, "")
                atualizar_medida(metadedobra5_entry, "")
                return
            else:
                medidadobra5 = float(dobra5.get()) - (deducao_valor / 2)
                atualizar_medida(medidadobra5_entry, medidadobra5)

    def metade_dobra():
        entradas = [
            (medidadobra1_entry, metadedobra1_entry),
            (medidadobra2_entry, metadedobra2_entry),
            (medidadobra3_entry, metadedobra3_entry),
            (medidadobra4_entry, metadedobra4_entry),
            (medidadobra5_entry, metadedobra5_entry)
        ]

        for medidadobra_entry, metadedobra_entry in entradas:
            medidadobra_entry.config(state='normal')
            try:
                medidadobra = float(medidadobra_entry.get())
                metadedobra = medidadobra / 2
                atualizar_medida(metadedobra_entry, metadedobra)
            except ValueError:
                return
            finally:
                medidadobra_entry.config(state='readonly')


    def limpar_dobras():
        limpar_dobras = [dobra1, dobra2, dobra3, dobra4, dobra5]
        limpar_medidas = [medidadobra1_entry, medidadobra2_entry, medidadobra3_entry, medidadobra4_entry, medidadobra5_entry]
        limpar_metades = [metadedobra1_entry, metadedobra2_entry, metadedobra3_entry, metadedobra4_entry, metadedobra5_entry]

        for limpar_dobras in limpar_dobras:
            limpar_dobras.delete(0, tk.END)

        for limpar_medidas in limpar_medidas:
            limpar_medidas.config(state='normal')
            limpar_medidas.delete(0, tk.END)
            limpar_medidas.config(state='readonly')

        for limpar_metades in limpar_metades:
            limpar_metades.config(state='normal')
            limpar_metades.delete(0, tk.END)
            limpar_metades.config(state='readonly')

    def limpar_tudo():
        espessura_combobox.set('')
        material_combobox.set('')
        canal_combobox.set('')
        raio_interno_valor.delete(0, tk.END)
        fator_k_entry.delete(0, tk.END)
        deducao_entry.delete(0, tk.END)
        limpar_dobras()

    def calcular():
        calcular_dobra()
        metade_dobra()
        print(deducao_entry.get())

    # Layout
    aba1 = ttk.Frame(notebook, width=400, height=400)
    aba1.pack(fill='both', expand=True)
    notebook.add(aba1, text='Aba 1')

    # Novo frame para entradas de valores de dobra
    frame_dobras = tk.Frame(aba1)
    frame_dobras.pack(padx=10, pady=10)

    # Labels para as entradas de valores de dobra
    dobra1_label = tk.Label(frame_dobras, text="Dobra 1:")
    dobra1_label.grid(row=0, column=0, padx=5, pady=5)
    dobra2_label = tk.Label(frame_dobras, text="Dobra 2:")
    dobra2_label.grid(row=1, column=0, padx=5, pady=5)
    dobra3_label = tk.Label(frame_dobras, text="Dobra 3:")
    dobra3_label.grid(row=2, column=0, padx=5, pady=5)
    dobra4_label = tk.Label(frame_dobras, text="Dobra 4:")
    dobra4_label.grid(row=3, column=0, padx=5, pady=5)
    dobra5_label = tk.Label(frame_dobras, text="Dobra 5:")
    dobra5_label.grid(row=4, column=0, padx=5, pady=5)

    # Entradas para inserir valores de dobra
    dobra1 = tk.Entry(frame_dobras)
    dobra1.grid(row=0, column=1, padx=5, pady=5)
    dobra2 = tk.Entry(frame_dobras)
    dobra2.grid(row=1, column=1, padx=5, pady=5)
    dobra3 = tk.Entry(frame_dobras)
    dobra3.grid(row=2, column=1, padx=5, pady=5)
    dobra4 = tk.Entry(frame_dobras)
    dobra4.grid(row=3, column=1, padx=5, pady=5)
    dobra5 = tk.Entry(frame_dobras)
    dobra5.grid(row=4, column=1, padx=5, pady=5)

    # Medida da linha de dobra
    medidadobra1_entry = tk.Entry(frame_dobras, state='readonly')
    medidadobra1_entry.grid(row=0, column=2, padx=5, pady=5)
    medidadobra2_entry = tk.Entry(frame_dobras, state='readonly')
    medidadobra2_entry.grid(row=1, column=2, padx=5, pady=5)
    medidadobra3_entry = tk.Entry(frame_dobras, state='readonly')
    medidadobra3_entry.grid(row=2, column=2, padx=5, pady=5)
    medidadobra4_entry = tk.Entry(frame_dobras, state='readonly')
    medidadobra4_entry.grid(row=3, column=2, padx=5, pady=5)
    medidadobra5_entry = tk.Entry(frame_dobras, state='readonly')
    medidadobra5_entry.grid(row=4, column=2, padx=5, pady=5)

    # Medida da linha de dobra
    metadedobra1_entry = tk.Entry(frame_dobras, state='readonly')
    metadedobra1_entry.grid(row=0, column=3, padx=5, pady=5)
    metadedobra2_entry = tk.Entry(frame_dobras, state='readonly')
    metadedobra2_entry.grid(row=1, column=3, padx=5, pady=5)
    metadedobra3_entry = tk.Entry(frame_dobras, state='readonly')
    metadedobra3_entry.grid(row=2, column=3, padx=5, pady=5)
    metadedobra4_entry = tk.Entry(frame_dobras, state='readonly')
    metadedobra4_entry.grid(row=3, column=3, padx=5, pady=5)
    metadedobra5_entry = tk.Entry(frame_dobras, state='readonly')
    metadedobra5_entry.grid(row=4, column=3, padx=5, pady=5)

    # Botão para limpar valores de dobras
    limpar_dobras_button = tk.Button(aba1, text="Limpar Dobras", command=limpar_dobras)
    limpar_dobras_button.pack(pady=10)
    # Botão para limpar todos os valores
    limpar_tudo_button = tk.Button(aba1, text="Limpar Tudo", command=limpar_tudo)
    limpar_tudo_button.pack(pady=10)

    # Inicializar comboboxes
    material_combobox = ttk.Combobox(frame_dobras)
    espessura_combobox = ttk.Combobox(frame_dobras)
    canal_combobox = ttk.Combobox(frame_dobras)
    deducao_entry = tk.Entry(frame_dobras)
    raio_interno_valor = tk.Entry(frame_dobras)
    fator_k_entry = tk.Entry(frame_dobras, state='readonly')

    deducao_entry.bind("<KeyRelease>", lambda event: calcular())

    dobra1.bind("<KeyRelease>", lambda event: calcular())
    dobra2.bind("<KeyRelease>", lambda event: calcular())
    dobra3.bind("<KeyRelease>", lambda event: calcular())
    dobra4.bind("<KeyRelease>", lambda event: calcular())
    dobra5.bind("<KeyRelease>", lambda event: calcular())
    