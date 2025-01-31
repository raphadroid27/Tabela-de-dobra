import tkinter as tk
from tkinter import messagebox
from models import canal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    def adicionar_canal():
        valor_canal = canal_valor_entry.get()
        largura_canal = canal_largura_entry.get()
        altura_canal = canal_altura_entry.get()
        comprimento_total_canal = canal_comprimento_total_entry.get()
        observacao_canal = canal_observacao_entry.get()
        
        if not valor_canal:
            messagebox.showerror("Erro", "O campo Canal é obrigatório.")
            return
        
        canal_existente = session.query(canal).filter_by(valor=valor_canal).first()
        if not canal_existente:
            novo_canal = canal(
                valor=valor_canal,
                largura=float(largura_canal) if largura_canal else None,
                altura=float(altura_canal) if altura_canal else None,
                comprimento_total=float(comprimento_total_canal) if comprimento_total_canal else None,
                observacao=observacao_canal if observacao_canal else None
            )
            session.add(novo_canal)
            session.commit()
            canal_valor_entry.delete(0, tk.END)
            canal_largura_entry.delete(0, tk.END)
            canal_altura_entry.delete(0, tk.END)
            canal_comprimento_total_entry.delete(0, tk.END)
            canal_observacao_entry.delete(0, tk.END)
            messagebox.showinfo("Sucesso", "Novo canal adicionado com sucesso!")
        else:
            messagebox.showerror("Erro", "Canal já existe no banco de dados.")

    root = tk.Tk()
    root.title("Adicionar Novo Canal")
    root.geometry("300x260")
    root.resizable(False, False)

    main_frame = tk.Frame(root)
    main_frame.pack(pady=20, padx=20)

    tk.Label(main_frame, text="Canal:", anchor="w").grid(row=0, column=0, sticky="w")
    canal_valor_entry = tk.Entry(main_frame)
    canal_valor_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Largura:", anchor="w").grid(row=1, column=0, sticky="w")
    canal_largura_entry = tk.Entry(main_frame)
    canal_largura_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Altura:", anchor="w").grid(row=2, column=0, sticky="w")
    canal_altura_entry = tk.Entry(main_frame)
    canal_altura_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Comprimento Total:", anchor="w").grid(row=3, column=0, sticky="w")
    canal_comprimento_total_entry = tk.Entry(main_frame)
    canal_comprimento_total_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Observação:", anchor="w").grid(row=4, column=0, sticky="w")
    canal_observacao_entry = tk.Entry(main_frame)
    canal_observacao_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Adicionar Canal", command=adicionar_canal).grid(row=5, column=0, columnspan=2, pady=10)

    aviso_label = tk.Label(root, text="", font=("Helvetica", 10))
    aviso_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main(None)