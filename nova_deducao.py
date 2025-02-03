import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
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
    root.title("Adicionar Nova Dedução")
    root.resizable(False, False)

    # Posicionar a janela nova_deducao em relação à janela principal
    root.update_idletasks() 
    x = root_app.winfo_x() + root_app.winfo_width() + 10
    y = root_app.winfo_y()
    root.geometry(f"+{x}+{y}")

    root.update_idletasks() 
    print(f"{root.winfo_width()}x{root.winfo_height()}")

    # Frame principal para organizar as colunas
    main_frame = tk.Frame(root)
    main_frame.pack(pady=10, padx=10)

    tk.Label(main_frame, text="Material:", anchor="w").grid(row=0, column=0, sticky="w")
    g.deducao_material_combobox = ttk.Combobox(main_frame, values=[m.nome for m in session.query(material).all()])
    g.deducao_material_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    
    tk.Label(main_frame, text="Espessura:", anchor="w").grid(row=1, column=0, sticky="w")
    g.deducao_espessura_combobox = ttk.Combobox(main_frame, values=[m.valor for m in session.query(espessura).all()])
    g.deducao_espessura_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Canal:", anchor="w").grid(row=2, column=0, sticky="w")
    g.deducao_canal_combobox = ttk.Combobox(main_frame, values=[c.valor for c in session.query(canal).all()])
    g.deducao_canal_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Dedução:", anchor="w").grid(row=3, column=0, sticky="w")
    g.deducao_valor_entry = tk.Entry(main_frame)
    g.deducao_valor_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Observação:", anchor="w").grid(row=4, column=0, sticky="w")
    g.deducao_obs_entry = tk.Entry(main_frame)
    g.deducao_obs_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Força:", anchor="w").grid(row=5, column=0, sticky="w")
    g.deducao_forca_entry = tk.Entry(main_frame)
    g.deducao_forca_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Adicionar Dedução", command=adicionar_deducao_e_observacao).grid(row=6, column=0, columnspan=2, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main(None)