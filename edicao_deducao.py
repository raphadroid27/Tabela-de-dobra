import tkinter as tk
from tkinter import ttk
from models import deducao, espessura, material, canal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    def carregar_deducoes():
        deducoes = session.query(deducao).all()
        for d in deducoes:
            tree.insert("", "end", values=(d.id, d.espessura.valor, d.canal.valor, d.material.nome, d.valor, d.observacao))

    def editar_deducao():
        selected_item = tree.selection()[0]
        item = tree.item(selected_item)
        deducao_id = item['values'][0]
        deducao_obj = session.query(deducao).filter_by(id=deducao_id).first()

        deducao_obj.valor = float(deducao_valor_entry.get().replace(',', '.'))
        deducao_obj.observacao = deducao_obs_entry.get()
        session.commit()
        aviso_label.config(text="Dedução editada com sucesso!", fg="green")
        tree.item(selected_item, values=(deducao_obj.id, deducao_obj.espessura.valor, deducao_obj.canal.valor, deducao_obj.material.nome, deducao_obj.valor, deducao_obj.observacao))

    def excluir_deducao():
        selected_item = tree.selection()[0]
        item = tree.item(selected_item)
        deducao_id = item['values'][0]
        deducao_obj = session.query(deducao).filter_by(id=deducao_id).first()
        session.delete(deducao_obj)
        session.commit()
        tree.delete(selected_item)
        aviso_label.config(text="Dedução excluída com sucesso!", fg="green")

    root = tk.Tk()
    root.title("Editar/Excluir Dedução")
    root.geometry("500x500")
    root.resizable(False, False)

    main_frame = tk.Frame(root)
    main_frame.pack(pady=20, padx=20)

    columns = ("ID", "Espessura", "Canal", "Material", "Valor", "Observação")
    tree = ttk.Treeview(main_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.pack()

    carregar_deducoes()

    tk.Label(main_frame, text="Novo Valor:", anchor="w").pack()
    deducao_valor_entry = tk.Entry(main_frame)
    deducao_valor_entry.pack(padx=5, pady=5, fill="x")

    tk.Label(main_frame, text="Nova Observação:", anchor="w").pack()
    deducao_obs_entry = tk.Entry(main_frame)
    deducao_obs_entry.pack(padx=5, pady=5, fill="x")

    tk.Button(main_frame, text="Editar Dedução", command=editar_deducao).pack(pady=10)
    tk.Button(main_frame, text="Excluir Dedução", command=excluir_deducao).pack(pady=10)

    aviso_label = tk.Label(root, text="", font=("Helvetica", 10))
    aviso_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main(None)
