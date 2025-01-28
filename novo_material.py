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

    def adicionar_material():
        aviso_label.config(text="", fg="red")  # Limpar aviso anterior
        nome_material = material_nome_entry.get()
        densidade_material = material_densidade_entry.get()
        escoamento_material = material_escoamento_entry.get()
        elasticidade_material = material_elasticidade_entry.get()
        
        if not nome_material:
            aviso_label.config(text="O campo Material é obrigatório.", fg="red")
            return
        
        material_existente = session.query(material).filter_by(nome=nome_material).first()
        if not material_existente:
            novo_material = material(
                nome=nome_material, 
                densidade=float(densidade_material) if densidade_material else None, 
                escoamento=float(escoamento_material) if escoamento_material else None, 
                elasticidade=float(elasticidade_material) if elasticidade_material else None
            )
            session.add(novo_material)
            session.commit()
            material_nome_entry.delete(0, tk.END)
            material_densidade_entry.delete(0, tk.END)
            material_escoamento_entry.delete(0, tk.END)
            material_elasticidade_entry.delete(0, tk.END)
            aviso_label.config(text="Novo material adicionado com sucesso!", fg="green")
        else:
            aviso_label.config(text="Material já existe no banco de dados.", fg="red")

    root = tk.Tk()
    root.title("Adicionar Novo Material")
    root.geometry("300x240")
    root.resizable(False, False)
    root.update_idletasks()
    root.geometry(f"{root.winfo_width()}x{root.winfo_height()}")

    main_frame = tk.Frame(root)
    main_frame.pack(pady=20, padx=20)

    tk.Label(main_frame, text="Material:", anchor="w").grid(row=0, column=0, sticky="w")
    material_nome_entry = tk.Entry(main_frame)
    material_nome_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Densidade:", anchor="w").grid(row=1, column=0, sticky="w")
    material_densidade_entry = tk.Entry(main_frame)
    material_densidade_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Escoamento:", anchor="w").grid(row=2, column=0, sticky="w")
    material_escoamento_entry = tk.Entry(main_frame)
    material_escoamento_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Elasticidade:", anchor="w").grid(row=3, column=0, sticky="w")
    material_elasticidade_entry = tk.Entry(main_frame)
    material_elasticidade_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Adicionar Material", command=adicionar_material).grid(row=4, column=0, columnspan=2, pady=10)

    aviso_label = tk.Label(root, text="", font=("Helvetica", 10))
    aviso_label.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main(None)