import tkinter as tk
from models import canal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    def adicionar_canal():
        aviso_label.config(text="", fg="red")  # Limpar aviso anterior
        valor_canal = float(canal_valor_entry.get())
        largura_canal = float(canal_largura_entry.get())
        altura_canal = float(canal_altura_entry.get())
        comprimento_total_canal = float(canal_comprimento_total_entry.get())
        observacao_canal = canal_observacao_entry.get()
        canal_existente = session.query(canal).filter_by(valor=valor_canal).first()
        if not canal_existente:
            novo_canal = canal(
                valor=valor_canal,
                largura=largura_canal,
                altura=altura_canal,
                comprimento_total=comprimento_total_canal,
                observacao=observacao_canal
            )
            session.add(novo_canal)
            session.commit()
            canal_valor_entry.delete(0, tk.END)
            canal_largura_entry.delete(0, tk.END)
            canal_altura_entry.delete(0, tk.END)
            canal_comprimento_total_entry.delete(0, tk.END)
            canal_observacao_entry.delete(0, tk.END)
            aviso_label.config(text="Novo canal adicionado com sucesso!", fg="green")
        else:
            aviso_label.config(text="Canal já existe no banco de dados.", fg="red")

    root = tk.Tk()
    root.title("Adicionar Novo Canal")
    root.geometry("400x300")
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