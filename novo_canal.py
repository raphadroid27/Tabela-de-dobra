import tkinter as tk
from tkinter import messagebox
from models import canal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import globals as g
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    root = tk.Tk()
    root.title("Adicionar Novo Canal")
    root.resizable(False, False)

    # Posicionar a janela nova_deducao em relação à janela principal
    root.update_idletasks() 
    x = root_app.winfo_x() + root_app.winfo_width() + 10
    y = root_app.winfo_y()
    root.geometry(f"+{x}+{y}")

    main_frame = tk.Frame(root)
    main_frame.pack(pady=10, padx=10)

    tk.Label(main_frame, text="Canal:", anchor="w").grid(row=0, column=0, sticky="w")
    g.canal_valor_entry = tk.Entry(main_frame)
    g.canal_valor_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Largura:", anchor="w").grid(row=1, column=0, sticky="w")
    g.canal_largura_entry = tk.Entry(main_frame)
    g.canal_largura_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Altura:", anchor="w").grid(row=2, column=0, sticky="w")
    g.canal_altura_entry = tk.Entry(main_frame)
    g.canal_altura_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Comprimento Total:", anchor="w").grid(row=3, column=0, sticky="w")
    g.canal_comprimento_entry = tk.Entry(main_frame)
    g.canal_comprimento_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Observação:", anchor="w").grid(row=4, column=0, sticky="w")
    g.canal_observacao_entry = tk.Entry(main_frame)
    g.canal_observacao_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Adicionar Canal", command=adicionar_canal).grid(row=5, column=0, columnspan=2, pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main(None)