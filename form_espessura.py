import tkinter as tk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    root = tk.Tk()
    root.title("Adicionar Nova Espessura")
    root.resizable(False, False)

    # Posicionar a janela nova_deducao em relação à janela principal
    root.update_idletasks() 
    x = root_app.winfo_x() + root_app.winfo_width() + 10
    y = root_app.winfo_y()
    root.geometry(f"+{x}+{y}")

    root.update_idletasks() 
    print(f"{root.winfo_width()}x{root.winfo_height()}")


    main_frame = tk.Frame(root)
    main_frame.pack(pady=10, padx=10)

    tk.Label(main_frame, text="Espessura:", anchor="w").grid(row=0, column=0, sticky="w")
    g.espessura_valor_entry = tk.Entry(main_frame)
    g.espessura_valor_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Adicionar Espessura", command=adicionar_espessura).grid(row=1, column=0, columnspan=2, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main(None)