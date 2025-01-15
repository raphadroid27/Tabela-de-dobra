import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

def configuracao_do_banco_de_dados():
    engine = create_engine('sqlite:///tabela_de_dobra.db')
    Session = sessionmaker(bind=engine)
    return Session()

def atualizar_medida(entry, valor):
        entry.config(state='normal')
        entry.delete(0, tk.END)
        entry.insert(0, valor)
        entry.config(state='readonly')

def cabecalho(root):

    session = configuracao_do_banco_de_dados()

    def atualizar_espessura():
        material_nome = material_combobox.get()
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        if material_obj:
            espessuras_nomes = [str(e.nome) for e in session.query(espessura).join(deducao).filter(deducao.material_id == material_obj.id).all()]
            espessura_combobox['values'] = espessuras_nomes

    def atualizar_canal():
        espessura_nome = espessura_combobox.get()
        espessura_obj = session.query(espessura).filter_by(nome=espessura_nome).first()
        if espessura_obj:
            canais_valores = [str(c.valor) for c in session.query(canal).join(deducao).filter(deducao.espessura_id == espessura_obj.id).all()]
            canal_combobox['values'] = canais_valores

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

    def calcular_fatork():
        if raio_interno_valor.get() == "":
            atualizar_medida(fator_k_entry, "")
            print('Raio interno vazio')
            return
        else:
            deducao_valor = float(deducao_entry.get())
            espessura_nome = espessura_combobox.get()
            espessura_obj = session.query(espessura).filter_by(nome=espessura_nome).first()
            espessura_valor = espessura_obj.valor
            raio_interno = float(raio_interno_valor.get().replace(',', '.'))

            fator_k = (4 * (espessura_valor - (deducao_valor / 2) + raio_interno) - (3.14159 * raio_interno)) / (3.14159 * espessura_valor)

            atualizar_medida(fator_k_entry, f"{fator_k:.2f}")

            print('Calculando fator K')            

    def atualizar():
        atualizar_espessura()
        atualizar_canal()
        atualizar_deducao()
        calcular_fatork()
        

    cabecalho = ttk.Frame(root, width=400, height=400)
    cabecalho.pack(fill='both', expand=True)

    # Definir a largura fixa para os frames
    frame_width = 300

    # Primeira linha frame
    input_frame = tk.Frame(cabecalho, width=frame_width)
    input_frame.pack(padx=10, pady=0, fill='x', expand=True)

    input_frame.grid_columnconfigure(0, weight=1, minsize=frame_width/3)
    input_frame.grid_columnconfigure(1, weight=1, minsize=frame_width/3)
    input_frame.grid_columnconfigure(2, weight=1, minsize=frame_width/3)

    material_label = tk.Label(input_frame, text="Material:")
    material_label.grid(row=0, column=0, sticky='ew')

    material_combobox = ttk.Combobox(input_frame, values=[m.nome for m in session.query(material).all()])
    material_combobox.grid(row=1, column=0, padx=10, sticky='ew')

    espessura_label = tk.Label(input_frame, text="Espessura: ")
    espessura_label.grid(row=0, column=1, sticky='ew')

    espessura_combobox = ttk.Combobox(input_frame)
    espessura_combobox.grid(row=1, column=1, padx=10, sticky='ew')

    canal_label = tk.Label(input_frame, text="Canal:")
    canal_label.grid(row=0, column=2, sticky='ew')

    canal_combobox = ttk.Combobox(input_frame)
    canal_combobox.grid(row=1, column=2, padx=10, sticky='ew')

    # Segunda linha frame
    results_frame = tk.Frame(cabecalho, width=frame_width)
    results_frame.pack(padx=10, pady=10, fill='x', expand=True)

    # Configurar a largura das colunas do grid
    results_frame.grid_columnconfigure(0, weight=1, minsize=frame_width/4)
    results_frame.grid_columnconfigure(1, weight=1, minsize=frame_width/4)
    results_frame.grid_columnconfigure(2, weight=1, minsize=frame_width/4)
    results_frame.grid_columnconfigure(3, weight=1, minsize=frame_width/4)

    # Raio interno
    raio_interno_label = tk.Label(results_frame, text="Raio Interno: ")
    raio_interno_label.grid(row=0, column=0, padx=10, sticky='ew')

    raio_interno_valor = tk.Entry(results_frame)
    raio_interno_valor.grid(row=1, column=0, padx=10, sticky='ew')

    # Fator K
    fator_k_label = tk.Label(results_frame, text="Fator K: ")
    fator_k_label.grid(row=0, column=1, padx=10, sticky='ew')

    fator_k_entry = tk.Entry(results_frame, state='readonly')
    fator_k_entry.grid(row=1, column=1, padx=10, sticky='ew')

    # Dedução
    deducao_label = tk.Label(results_frame, text="Dedução: ")
    deducao_label.grid(row=0, column=2, padx=10, sticky='ew')

    deducao_entry = tk.Entry(results_frame)
    deducao_entry.grid(row=1, column=2, padx=10, sticky='ew')

    # Offset
    offset_label = tk.Label(results_frame, text="Offset: ")
    offset_label.grid(row=0, column=3, padx=10, sticky='ew')

    offset_entry = tk.Entry(results_frame)
    offset_entry.grid(row=1, column=3, padx=10, sticky='ew')

    canal_combobox.bind("<<ComboboxSelected>>", lambda event: atualizar())
    espessura_combobox.bind("<<ComboboxSelected>>", lambda event: atualizar())
    material_combobox.bind("<<ComboboxSelected>>", lambda event: atualizar())

    raio_interno_valor.bind("<KeyRelease>", lambda event: atualizar())