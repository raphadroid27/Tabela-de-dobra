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

    def adicionar_material():
        nome = material_nome_entry.get()
        densidade = float(material_densidade_entry.get())
        novo_material = material(nome=nome, densidade=densidade)
        session.add(novo_material)
        session.commit()
        material_nome_entry.delete(0, tk.END)
        material_densidade_entry.delete(0, tk.END)

    def adicionar_espessura():
        nome = espessura_nome_entry.get()
        valor = float(espessura_valor_entry.get())
        material_nome = espessura_material_combobox.get()
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        nova_espessura = espessura(nome=nome, valor=valor, material_id=material_obj.id)
        session.add(nova_espessura)
        session.commit()
        espessura_nome_entry.delete(0, tk.END)
        espessura_valor_entry.delete(0, tk.END)
        espessura_material_combobox.set('')

    def adicionar_canal():
        nome = canal_nome_entry.get()
        valor = float(canal_valor_entry.get())
        espessura_nome = canal_espessura_combobox.get()
        espessura_obj = session.query(espessura).filter_by(nome=espessura_nome).first()
        novo_canal = canal(nome=nome, valor=valor, espessura_id=espessura_obj.id)
        session.add(novo_canal)
        session.commit()
        canal_nome_entry.delete(0, tk.END)
        canal_valor_entry.delete(0, tk.END)
        canal_espessura_combobox.set('')

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

    root = tk.Tk()
    root.title("Tabela de dobra")
    root.geometry("600x600")
    root.resizable(False, False)

    label1 = tk.Label(root, text="Adicionar Nova Dedução de Dobra", font=("Helvetica", 16))
    label1.pack(pady=10)

    # Formulário para adicionar material
    material_frame = tk.Frame(root)
    material_frame.pack(pady=10)
    tk.Label(material_frame, text="Nome do Material:").grid(row=0, column=0)
    material_nome_entry = tk.Entry(material_frame)
    material_nome_entry.grid(row=0, column=1)
    tk.Label(material_frame, text="Densidade:").grid(row=1, column=0)
    material_densidade_entry = tk.Entry(material_frame)
    material_densidade_entry.grid(row=1, column=1)
    tk.Button(material_frame, text="Adicionar Material", command=adicionar_material).grid(row=2, columnspan=2, pady=5)

    # Formulário para adicionar espessura
    espessura_frame = tk.Frame(root)
    espessura_frame.pack(pady=10)
    tk.Label(espessura_frame, text="Nome da Espessura:").grid(row=0, column=0)
    espessura_nome_entry = tk.Entry(espessura_frame)
    espessura_nome_entry.grid(row=0, column=1)
    tk.Label(espessura_frame, text="Valor:").grid(row=1, column=0)
    espessura_valor_entry = tk.Entry(espessura_frame)
    espessura_valor_entry.grid(row=1, column=1)
    tk.Label(espessura_frame, text="Material:").grid(row=2, column=0)
    materiais_nomes = [m.nome for m in session.query(material).all()]
    espessura_material_combobox = ttk.Combobox(espessura_frame, values=materiais_nomes)
    espessura_material_combobox.grid(row=2, column=1)
    tk.Button(espessura_frame, text="Adicionar Espessura", command=adicionar_espessura).grid(row=3, columnspan=2, pady=5)

    # Formulário para adicionar canal
    canal_frame = tk.Frame(root)
    canal_frame.pack(pady=10)
    tk.Label(canal_frame, text="Nome do Canal:").grid(row=0, column=0)
    canal_nome_entry = tk.Entry(canal_frame)
    canal_nome_entry.grid(row=0, column=1)
    tk.Label(canal_frame, text="Valor:").grid(row=1, column=0)
    canal_valor_entry = tk.Entry(canal_frame)
    canal_valor_entry.grid(row=1, column=1)
    tk.Label(canal_frame, text="Espessura:").grid(row=2, column=0)
    espessuras_nomes = [e.nome for e in session.query(espessura).all()]
    canal_espessura_combobox = ttk.Combobox(canal_frame, values=espessuras_nomes)
    canal_espessura_combobox.grid(row=2, column=1)
    tk.Button(canal_frame, text="Adicionar Canal", command=adicionar_canal).grid(row=3, columnspan=2, pady=5)

    # Formulário para adicionar dedução
    deducao_frame = tk.Frame(root)
    deducao_frame.pack(pady=10)
    tk.Label(deducao_frame, text="Espessura:").grid(row=0, column=0)
    deducao_espessura_combobox = ttk.Combobox(deducao_frame, values=espessuras_nomes)
    deducao_espessura_combobox.grid(row=0, column=1)
    tk.Label(deducao_frame, text="Canal:").grid(row=1, column=0)
    canais_nomes = [c.nome for c in session.query(canal).all()]
    deducao_canal_combobox = ttk.Combobox(deducao_frame, values=canais_nomes)
    deducao_canal_combobox.grid(row=1, column=1)
    tk.Label(deducao_frame, text="Material:").grid(row=2, column=0)
    deducao_material_combobox = ttk.Combobox(deducao_frame, values=materiais_nomes)
    deducao_material_combobox.grid(row=2, column=1)
    tk.Label(deducao_frame, text="Valor:").grid(row=3, column=0)
    deducao_valor_entry = tk.Entry(deducao_frame)
    deducao_valor_entry.grid(row=3, column=1)
    tk.Button(deducao_frame, text="Adicionar Dedução", command=adicionar_deducao).grid(row=4, columnspan=2, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()