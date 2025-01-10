import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main():


    def adicionar_deducao():
        espessura_nome = deducao_espessura_combobox.get()
        canal_nome = deducao_canal_combobox.get()
        material_nome = deducao_material_combobox.get()
        valor = float(deducao_valor_entry.get())
        espessura_obj = session.query(espessura).filter_by(nome=espessura_nome).first()
        canal_obj = session.query(canal).filter_by(nome=canal_nome).first()
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        nova_deducao = deducao(espessura_id=espessura_obj.id, canal_id=canal_obj.id, material_id=material_obj.id, valor=valor)
        session.add(nova_deducao)
        session.commit()
        deducao_espessura_combobox.set('')
        deducao_canal_combobox.set('')
        deducao_material_combobox.set('')
        deducao_valor_entry.delete(0, tk.END)

    def adicionar_dados():
    # Adicionar novos valores ao banco de dados apenas se os campos estiverem preenchidos
        if material_nome_entry.get() and material_densidade_entry.get():
            nome_material = material_nome_entry.get()
            densidade_material = float(material_densidade_entry.get())
            novo_material = material(nome=nome_material, densidade=densidade_material)
            session.add(novo_material)
            material_nome_entry.delete(0, tk.END)
            material_densidade_entry.delete(0, tk.END)

        if espessura_nome_entry.get() and espessura_valor_entry.get():
            nome_espessura = espessura_nome_entry.get()
            valor_espessura = float(espessura_valor_entry.get())
            nova_espessura = espessura(nome=nome_espessura, valor=valor_espessura)
            session.add(nova_espessura)
            espessura_nome_entry.delete(0, tk.END)
            espessura_valor_entry.delete(0, tk.END)

        if canal_nome_entry.get() and canal_valor_entry.get():
            nome_canal = canal_nome_entry.get()
            valor_canal = float(canal_valor_entry.get())
            novo_canal = canal(nome=nome_canal, valor=valor_canal)
            session.add(novo_canal)
            canal_nome_entry.delete(0, tk.END)
            canal_valor_entry.delete(0, tk.END)

        session.commit()
        atualizar_dados()

    def atualizar_dados():
        # Atualizar valores dos comboboxes
        materiais = [m.nome for m in session.query(material).all()]
        espessuras = [e.nome for e in session.query(espessura).all()]
        canais = [c.nome for c in session.query(canal).all()]

        deducao_material_combobox['values'] = materiais
        deducao_espessura_combobox['values'] = espessuras
        deducao_canal_combobox['values'] = canais
    

    root = tk.Tk()
    root.title("Tabela de dobra")
    root.geometry("600x600")
    root.resizable(False, False)

    label1 = tk.Label(root, text="Adicionar Nova Dedução de Dobra", font=("Helvetica", 16))
    label1.pack(pady=10)

    # Frame principal para organizar as colunas
    main_frame = tk.Frame(root)
    main_frame.pack(pady=10)

    # Coluna "Nova Dedução"
    nova_deducao_frame = tk.Frame(main_frame)
    nova_deducao_frame.grid(row=0, column=0, padx=10)

    tk.Label(nova_deducao_frame, text="Nova Dedução").grid(row=0, column=0, columnspan=2)

    tk.Label(nova_deducao_frame, text="Material:").grid(row=1, column=0)
    deducao_material_combobox = ttk.Combobox(nova_deducao_frame, values=[m.nome for m in session.query(material).all()])
    deducao_material_combobox.grid(row=1, column=1)

    tk.Label(nova_deducao_frame, text="Espessura:").grid(row=2, column=0)
    deducao_espessura_combobox = ttk.Combobox(nova_deducao_frame, values=[m.nome for m in session.query(espessura).all()])
    deducao_espessura_combobox.grid(row=2, column=1)

    tk.Label(nova_deducao_frame, text="Canal:").grid(row=3, column=0)
    deducao_canal_combobox = ttk.Combobox(nova_deducao_frame, values=[])
    deducao_canal_combobox.grid(row=3, column=1)

    tk.Label(nova_deducao_frame, text="Dedução:").grid(row=4, column=0)
    deducao_valor_entry = tk.Entry(nova_deducao_frame)
    deducao_valor_entry.grid(row=4, column=1)

    tk.Button(nova_deducao_frame, text="Adicionar Dedução", command=adicionar_deducao).grid(row=5, columnspan=2, pady=5)

    # Coluna "Novos Valores"
    novos_valores_frame = tk.Frame(main_frame)
    novos_valores_frame.grid(row=0, column=1, padx=10)

    tk.Label(novos_valores_frame, text="Novos Valores").grid(row=0, column=0, columnspan=2)

    tk.Label(novos_valores_frame, text="Material:").grid(row=1, column=0)
    material_nome_entry = tk.Entry(novos_valores_frame)
    material_nome_entry.grid(row=1, column=1)

    tk.Label(novos_valores_frame, text="Densidade:").grid(row=2, column=0)
    material_densidade_entry = tk.Entry(novos_valores_frame)
    material_densidade_entry.grid(row=2, column=1)

    tk.Label(novos_valores_frame, text="Nome da Espessura:").grid(row=4, column=0)
    espessura_nome_entry = tk.Entry(novos_valores_frame)
    espessura_nome_entry.grid(row=4, column=1)

    tk.Label(novos_valores_frame, text="Valor:").grid(row=5, column=0)
    espessura_valor_entry = tk.Entry(novos_valores_frame)
    espessura_valor_entry.grid(row=5, column=1)

    tk.Label(novos_valores_frame, text="Nome do Canal:").grid(row=7, column=0)
    canal_nome_entry = tk.Entry(novos_valores_frame)
    canal_nome_entry.grid(row=7, column=1)

    tk.Label(novos_valores_frame, text="Valor:").grid(row=8, column=0)
    canal_valor_entry = tk.Entry(novos_valores_frame)
    canal_valor_entry.grid(row=8, column=1)

    tk.Button(novos_valores_frame, text="Adicionar Dados", command=adicionar_dados).grid(row=10, columnspan=2, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()