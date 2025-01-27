import tkinter as tk
from models import espessura
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    def adicionar_espessura():
        aviso_label.config(text="", fg="red")  # Limpar aviso anterior
        valor_espessura = float(espessura_valor_entry.get().replace(',', '.'))
        espessura_existente = session.query(espessura).filter_by(valor=valor_espessura).first()
        if not espessura_existente:
            nova_espessura = espessura(valor=valor_espessura)
            session.add(nova_espessura)
            session.commit()
            espessura_valor_entry.delete(0, tk.END)
            aviso_label.config(text="Nova espessura adicionada com sucesso!", fg="green")
        else:
            aviso_label.config(text="Espessura já existe no banco de dados.", fg="red")

    root = tk.Tk()
    root.title("Adicionar Nova Espessura")
    root.geometry("400x200")
    root.resizable(False, False)

    main_frame = tk.Frame(root)
    main_frame.pack(pady=20, padx=20)

    tk.Label(main_frame, text="Espessura:", anchor="w").grid(row=0, column=0, sticky="w")
    espessura_valor_entry = tk.Entry(main_frame)
    espessura_valor_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Adicionar Espessura", command=adicionar_espessura).grid(row=1, column=0, columnspan=2, pady=10)

    aviso_label = tk.Label(root, text="", font=("Helvetica", 10))
    aviso_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main(None)