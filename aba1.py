import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


def configuracao_do_banco_de_dados():
    engine = create_engine('sqlite:///tabela_de_dobra.db')
    Session = sessionmaker(bind=engine)
    return Session()

def criar_aba1(notebook):
    session = configuracao_do_banco_de_dados()

    aba1 = ttk.Frame(notebook, width=400, height=400)
    aba1.pack(fill='both', expand=True)
    notebook.add(aba1, text='Aba 1')

    frame = tk.Frame(aba1)
    frame.pack(padx=10, pady=10)

    material_label = tk.Label(frame, text="Material:")
    material_label.grid(row=0, column=0)

    material_combobox = ttk.Combobox(frame, values=[m.nome for m in session.query(material).all()])
    material_combobox.grid(row=1, column=0, padx=10)

    espessura_label = tk.Label(frame, text="Espessura: ")
    espessura_label.grid(row=0, column=1)
    
    espessura_combobox = ttk.Combobox(frame)
    espessura_combobox.grid(row=1, column=1, padx=10)

    canal_label = tk.Label(frame, text="Canal:")
    canal_label.grid(row=0, column=2)

    canal_combobox = ttk.Combobox(frame)
    canal_combobox.grid(row=1, column=2, padx=10)

    #Raio interno
    raio_interno_label = tk.Label(frame, text="Raio Interno: ")
    raio_interno_label.grid(row=3, column=0,padx=10)

    raio_interno_valor = tk.Entry(frame)
    raio_interno_valor.grid(row=4, column=0,padx=10)
    
    #Fator K
    fator_k_label = tk.Label(frame, text="Fator K: ")
    fator_k_label.grid(row=3, column=1,padx=10)

    fator_k_entry = tk.Entry(frame, state='readonly')
    fator_k_entry.grid(row=4, column=1,padx=10)

    #Dedução
    deducao_label = tk.Label(frame, text="Dedução: ")
    deducao_label.grid(row=3, column=2,padx=10)

    deducao_entry = tk.Entry(frame)
    deducao_entry.grid(row=4, column=2,padx=10)
    
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

    #Medida da linha de dobra

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

     #Medida da linha de dobra

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

    #Funções

    def atualizar_espessura():
        material_nome = material_combobox.get()
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        if material_obj:
            espessuras_nomes = [str(e.nome) for e in session.query(espessura).join(deducao).filter(deducao.material_id == material_obj.id).all()]
            espessura_combobox['values'] = espessuras_nomes

    def atualizar_canal():

        print("Atualizando canais")

        espessura_nome = espessura_combobox.get()
        espessura_obj = session.query(espessura).filter_by(nome=espessura_nome).first()
        if espessura_obj:
            canais_valores = [str(c.valor) for c in session.query(canal).join(deducao).filter(deducao.espessura_id == espessura_obj.id).all()]
            canal_combobox['values'] = canais_valores

    def atualizar_medida(entry, valor):
            entry.config(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, valor)
            entry.config(state='readonly')

    def atualizar_deducao():
        espessura_nome = espessura_combobox.get()
        material_nome = material_combobox.get()
        canal_nome = canal_combobox.get()

        espessura_obj = session.query(espessura).filter_by(nome=espessura_nome).first()
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        canal_obj = session.query(canal).filter_by(valor=canal_nome).first()

        if espessura_obj and material_obj and canal_obj:
            deducao_obj = session.query(deducao).join(espessura).join(material).join(canal).filter(
                deducao.espessura_id == espessura_obj.id,
                deducao.material_id == material_obj.id,
                deducao.canal_id == canal_obj.id
            ).first()

            if deducao_obj:
                deducao_entry.config(state='normal')
                deducao_entry.delete(0, tk.END)
                deducao_entry.insert(0, f"{deducao_obj.valor}")
            else:
                deducao_entry.config(state='normal')
                deducao_entry.delete(0, tk.END)
                deducao_entry.insert(0, "Não encontrada")

            
    def atualizar_medida(entry, valor):
        entry.config(state='normal')
        entry.delete(0, tk.END)
        entry.insert(0, valor)
        entry.config(state='readonly')

    def calcular_dobra():

        if deducao_entry.get() == "":
            return
        else:
            deducao_valor = float(deducao_entry.get())

            # Calculo da medida da linha de dobra 1
            if dobra1.get() == "":
                atualizar_medida(medidadobra1_entry, "")
                atualizar_medida(metadedobra1_entry, "")
                return
            else:
                medidadobra1 = float(dobra1.get()) - (deducao_valor / 2)
                atualizar_medida(medidadobra1_entry, medidadobra1)
                print(medidadobra1)

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

    def calcular_fatork():

        if raio_interno_valor.get() == "":
            atualizar_medida(fator_k_entry, "")
            return
        else:
            deducao_valor = float(deducao_entry.get())
            espessura_nome = espessura_combobox.get()
            espessura_obj = session.query(espessura).filter_by(nome=espessura_nome).first()
            espessura_valor = espessura_obj.valor
            raio_interno = float(raio_interno_valor.get().replace(',', '.'))

            fator_k = (4 * (espessura_valor - (deducao_valor / 2) + raio_interno) - (3.14159 * raio_interno)) / (3.14159 * espessura_valor)    

            atualizar_medida(fator_k_entry, f"{fator_k:.2f}")

            print(fator_k)

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

    def todas_funcoes():

        print("Chamando atualizar_canais()")
        atualizar_espessura()
        print("Chamando atualizar_deducao()")
        atualizar_canal()
        print("Chamando atualizar_deducao()")
        atualizar_deducao()
        print("Chamando calcular_dobra()")
        calcular_dobra()
        print("Chamando metade_dobra()")
        metade_dobra()
        print("Chamando calcular_fatork()")
        calcular_fatork()

    # Botão para limpar valores de dobras
    limpar_dobras_button = tk.Button(aba1, text="Limpar Dobras", command=limpar_dobras)
    limpar_dobras_button.pack(pady=10)
    # Botão para limpar todos os valores
    limpar_tudo_button = tk.Button(aba1, text="Limpar Tudo", command=limpar_tudo)
    limpar_tudo_button.pack(pady=10)
    
    canal_combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())
    espessura_combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())
    material_combobox.bind("<<ComboboxSelected>>", lambda event: todas_funcoes())

    deducao_entry.bind("<KeyRelease>", lambda event: todas_funcoes())

    dobra1.bind("<KeyRelease>", lambda event: todas_funcoes())
    dobra2.bind("<KeyRelease>", lambda event: todas_funcoes())
    dobra3.bind("<KeyRelease>", lambda event: todas_funcoes())
    dobra4.bind("<KeyRelease>", lambda event: todas_funcoes())
    dobra5.bind("<KeyRelease>", lambda event: todas_funcoes())

    raio_interno_valor.bind("<KeyRelease>", lambda event: todas_funcoes())
   