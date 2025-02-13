import tkinter as tk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from funcoes import *

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    g.espessura_form = tk.Toplevel()
    g.espessura_form.title("Adicionar Nova Espessura")
    g.espessura_form.resizable(False, False)

    def on_top_espessura():
        if g.on_top_var.get() == 1:
            g.espessura_form.attributes("-topmost", True)
        else:
            g.espessura_form.attributes("-topmost", False)
    
    on_top_espessura()

    # Posicionar a janela nova_deducao em relação à janela principal
    g.espessura_form.update_idletasks() 
    x = root_app.winfo_x() + root_app.winfo_width() + 10
    y = root_app.winfo_y()
    g.espessura_form.geometry(f"+{x}+{y}")

    g.espessura_form.update_idletasks() 
    print(f"{g.espessura_form.winfo_width()}x{g.espessura_form.winfo_height()}")


    main_frame = tk.Frame(g.espessura_form)
    main_frame.pack(pady=10, padx=10)

    tk.Label(main_frame, text="Espessura:", anchor="w").grid(row=0, column=0, sticky="w")
    g.espessura_valor_entry = tk.Entry(main_frame)
    g.espessura_valor_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Adicionar Espessura", command=nova_espessura).grid(row=1, column=0, columnspan=2, pady=10)

    g.espessura_form.mainloop()

if __name__ == "__main__":
    main(None)