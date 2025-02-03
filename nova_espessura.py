import tkinter as tk
from tkinter import messagebox
from models import espessura
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    def adicionar_espessura():
        valor_espessura = float(espessura_valor_entry.get().replace(',', '.'))
        espessura_existente = session.query(espessura).filter_by(valor=valor_espessura).first()
        if not espessura_existente:
            nova_espessura = espessura(valor=valor_espessura)
            session.add(nova_espessura)
            session.commit()
            espessura_valor_entry.delete(0, tk.END)
            messagebox.showinfo("Sucesso", "Nova espessura adicionada com sucesso!")
        else:
            messagebox.showerror("Erro", "Espessura já existe no banco de dados.")

    root = tk.Tk()
    root.title("Adicionar Nova Espessura")
    root.resizable(False, False)

    # Posicionar a janela nova_deducao em relação à janela principal
    root.update_idletasks() 
    x = root_app.winfo_x() + root_app.winfo_width() + 10
    y = root_app.winfo_y()
    root.geometry(f"+{x}+{y}")

    main_frame = tk.Frame(root)
    main_frame.pack(pady=10, padx=10)

    tk.Label(main_frame, text="Espessura:", anchor="w").grid(row=0, column=0, sticky="w")
    espessura_valor_entry = tk.Entry(main_frame)
    espessura_valor_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Adicionar Espessura", command=adicionar_espessura).grid(row=1, column=0, columnspan=2, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main(None)