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

# Conteúdo da Aba 1

    frame = tk.Frame(aba1)
    frame.pack(padx=10, pady=10)

    # Lista de espessuras
    espessuras_valores = [str(e.valor) for e in session.query(espessura).all()]

    espessura_label = tk.Label(frame, text="Espessura: ")
    espessura_label.grid(row=0, column=0)
    
    espessura_combobox = ttk.Combobox(frame, values=espessuras_valores)
    espessura_combobox.grid(row=1, column=0, padx=10)

    #lista de materiais

    materiais_nomes = [m.nome for m in session.query(material).all()]

    material_label = tk.Label(frame, text="Material:")
    material_label.grid(row=0, column=1)

    material_combobox = ttk.Combobox(frame, values=materiais_nomes)
    material_combobox.grid(row=1, column=1,padx=10)

    #lista de canais
    canais_valores = [str(c.valor) for c in session.query(canal).all()]

    canal_label = tk.Label(frame, text="Canal:")
    canal_label.grid(row=0, column=2)

    canal_combobox = ttk.Combobox(frame, values=canais_valores)
    canal_combobox.grid(row=1, column=2,padx=10)

    #Raio interno
    raio_interno_label = tk.Label(frame, text="Raio Interno: ")
    raio_interno_label.grid(row=3, column=0,padx=10)
    
    #Fator K
    fator_k_label = tk.Label(frame, text="Fator K: ")
    fator_k_label.grid(row=3, column=1,padx=10)

    fator_k_valor = tk.Entry(frame)
    fator_k_valor.grid(row=4, column=1,padx=10)

    #Dedução
    deducao_label = tk.Label(frame, text="Dedução: ")
    deducao_label.grid(row=3, column=2,padx=10)

    deducao_valor = tk.Entry(frame)
    deducao_valor.grid(row=4, column=2,padx=10)
    
    def atualizar_deducao():
        espessura_valor = float(espessura_combobox.get())
        material_nome = material_combobox.get()
        canal_valor = float(canal_combobox.get())

        deducao_obj = session.query(deducao).join(espessura).join(material).join(canal).filter(
            espessura.valor == espessura_valor,
            material.nome == material_nome,
            canal.valor == canal_valor
        ).first()

        if deducao_obj:
            deducao_valor.config(state='normal')
            deducao_valor.delete(0, tk.END)
            deducao_valor.insert(0, f"{deducao_obj.valor}")
            
        else:
            deducao_valor.config(state='normal')
            deducao_valor.delete(0, tk.END)
            deducao_valor.insert(0, "Não encontrada")
            

    # Botão para atualizar a dedução
    button = tk.Button(aba1, text="Atualizar Dedução", command=atualizar_deducao)
    button.pack(pady=10)

    # Novo frame para entradas de valores de dobra
    frame_dobras = tk.Frame(aba1)
    frame_dobras.pack(padx=10, pady=10)

    # Entradas para inserir valores de dobra
    dobra1 = tk.Entry(frame_dobras)
    dobra1.grid(row=0, column=0, padx=5, pady=5)
    dobra2 = tk.Entry(frame_dobras)
    dobra2.grid(row=1, column=0, padx=5, pady=5)
    dobra3 = tk.Entry(frame_dobras)
    dobra3.grid(row=2, column=0, padx=5, pady=5)
    dobra4 = tk.Entry(frame_dobras)
    dobra4.grid(row=3, column=0, padx=5, pady=5)
    dobra5 = tk.Entry(frame_dobras)
    dobra5.grid(row=4, column=0, padx=5, pady=5)

if __name__ == "__main__":
    criar_aba1()