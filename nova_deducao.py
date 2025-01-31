import tkinter as tk
from tkinter import ttk, messagebox
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import app

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    def adicionar_deducao_e_observacao():
        espessura_valor = deducao_espessura_combobox.get()
        canal_valor = deducao_canal_combobox.get()
        material_nome = deducao_material_combobox.get()
        nova_deducao_valor = float(deducao_valor_entry.get().replace(',', '.'))
        espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
        canal_obj = session.query(canal).filter_by(valor=canal_valor).first()
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        
        nova_observacao_valor = deducao_obs_entry.get()
        nova_forca_valor = deducao_forca_entry.get()

        # Verificar se a dedução já existe
        deducao_existente = session.query(deducao).filter_by(
            espessura_id=espessura_obj.id,
            canal_id=canal_obj.id,
            material_id=material_obj.id
        ).first()

        if not deducao_existente:
            nova_deducao = deducao(
                espessura_id=espessura_obj.id,
                canal_id=canal_obj.id,
                material_id=material_obj.id,
                valor=nova_deducao_valor,
                observacao=nova_observacao_valor,
                forca=nova_forca_valor
            )
            session.add(nova_deducao)
            session.commit()
            messagebox.showinfo("Sucesso", "Nova dedução adicionada com sucesso!")
        else:
            messagebox.showerror("Erro", "Dedução já existe no banco de dados.")

        deducao_espessura_combobox.set('')
        deducao_canal_combobox.set('')
        deducao_material_combobox.set('')
        deducao_valor_entry.delete(0, tk.END)
        deducao_obs_entry.delete(0, tk.END)
        deducao_forca_entry.delete(0, tk.END)
    
    def on_closing():
        if root_app.winfo_exists():    
            root_app.destroy()
            root.destroy()
            app.main()

    root = tk.Tk()
    root.title("Tabela de dobra")
    root.geometry("300x260")
    root.resizable(False, False)
    root.update_idletasks()
    root.geometry(f"{root.winfo_width()}x{root.winfo_height()}")

    # Centralizar a janela add_form em relação à janela principal
    x = root_app.winfo_x() + (root_app.winfo_width() // 2) - (300 // 2)
    y = root_app.winfo_y() + (root_app.winfo_height() // 2) - (260 // 2)
    root.geometry(f"+{x}+{y}")

    # Frame principal para organizar as colunas
    main_frame = tk.Frame(root)
    main_frame.pack(pady=10, padx=10)

    tk.Label(main_frame, text="Material:", anchor="w").grid(row=0, column=0, sticky="w")
    deducao_material_combobox = ttk.Combobox(main_frame, values=[m.nome for m in session.query(material).all()])
    deducao_material_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    
    tk.Label(main_frame, text="Espessura:", anchor="w").grid(row=1, column=0, sticky="w")
    deducao_espessura_combobox = ttk.Combobox(main_frame, values=[m.valor for m in session.query(espessura).all()])
    deducao_espessura_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Canal:", anchor="w").grid(row=2, column=0, sticky="w")
    deducao_canal_combobox = ttk.Combobox(main_frame, values=[c.valor for c in session.query(canal).all()])
    deducao_canal_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Dedução:", anchor="w").grid(row=3, column=0, sticky="w")
    deducao_valor_entry = tk.Entry(main_frame)
    deducao_valor_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Observação:", anchor="w").grid(row=4, column=0, sticky="w")
    deducao_obs_entry = tk.Entry(main_frame)
    deducao_obs_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

    tk.Label(main_frame, text="Força:", anchor="w").grid(row=5, column=0, sticky="w")
    deducao_forca_entry = tk.Entry(main_frame)
    deducao_forca_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

    tk.Button(main_frame, text="Adicionar Dedução", command=adicionar_deducao_e_observacao).grid(row=6, column=0, columnspan=2, pady=10)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main(None)