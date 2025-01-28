import tkinter as tk
from tkinter import ttk
from models import material
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    def carregar_materiais():
        materiais = session.query(material).all()
        for m in materiais:
            tree.insert("", "end", values=(m.id, m.nome, m.densidade, m.escoamento, m.elasticidade))

    def editar_material():
        selected_item = tree.selection()[0]
        item = tree.item(selected_item)
        material_id = item['values'][0]
        material_obj = session.query(material).filter_by(id=material_id).first()

        material_obj.nome = material_nome_entry.get()
        material_obj.densidade = float(material_densidade_entry.get().replace(',', '.'))
        material_obj.escoamento = float(material_escoamento_entry.get().replace(',', '.'))
        material_obj.elasticidade = float(material_elasticidade_entry.get().replace(',', '.'))
        session.commit()
        aviso_label.config(text="Material editado com sucesso!", fg="green")
        tree.item(selected_item, values=(material_obj.id, material_obj.nome, material_obj.densidade, material_obj.escoamento, material_obj.elasticidade))

    def excluir_material():
        selected_item = tree.selection()[0]
        item = tree.item(selected_item)
        material_id = item['values'][0]
        material_obj = session.query(material).filter_by(id=material_id).first()
        session.delete(material_obj)
        session.commit()
        tree.delete(selected_item)
        aviso_label.config(text="Material excluído com sucesso!", fg="green")

    root = tk.Tk()
    root.title("Editar/Excluir Material")
    root.geometry("500x500")
    root.resizable(False, False)

    main_frame = tk.Frame(root)
    main_frame.pack(pady=20, padx=20)

    columns = ("ID", "Nome", "Densidade", "Escoamento", "Elasticidade")
    tree = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.pack()

    carregar_materiais()

    tk.Label(main_frame, text="Novo Nome:", anchor="w").pack()
    material_nome_entry = tk.Entry(main_frame)
    material_nome_entry.pack(padx=5, pady=5, fill="x")

    tk.Label(main_frame, text="Nova Densidade:", anchor="w").pack()
    material_densidade_entry = tk.Entry(main_frame)
    material_densidade_entry.pack(padx=5, pady=5, fill="x")

    tk.Label(main_frame, text="Novo Escoamento:", anchor="w").pack()
    material_escoamento_entry = tk.Entry(main_frame)
    material_escoamento_entry.pack(padx=5, pady=5, fill="x")

    tk.Label(main_frame, text="Nova Elasticidade:", anchor="w").pack()
    material_elasticidade_entry = tk.Entry(main_frame)
    material_elasticidade_entry.pack(padx=5, pady=5, fill="x")

    tk.Button(main_frame, text="Editar Material", command=editar_material).pack(pady=10)
    tk.Button(main_frame, text="Excluir Material", command=excluir_material).pack(pady=10)

    aviso_label = tk.Label(root, text="", font=("Helvetica", 10))
    aviso_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main(None)
