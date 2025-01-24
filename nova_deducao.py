import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao,observacao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import app

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

def main(root_app):

    def adicionar_deducao_e_observacao():
        aviso_label.config(text="", fg="red")  # Limpar aviso anterior
        espessura_valor = deducao_espessura_combobox.get()
        canal_valor = deducao_canal_combobox.get()
        material_nome = deducao_material_combobox.get()
        nova_deducao_valor = float(deducao_valor_entry.get().replace(',', '.'))
        espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
        canal_obj = session.query(canal).filter_by(valor=canal_valor).first()
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        
        nova_observacao_valor = deducao_obs_entry.get()
        nova_observacao = None
        if nova_observacao_valor:
            nova_observacao = session.query(observacao).filter_by(valor=nova_observacao_valor).first()
            if not nova_observacao:
                nova_observacao = observacao(valor=nova_observacao_valor)
                session.add(nova_observacao)
                session.commit()

        # Verificar se a dedução já existe (sem verificar o obs_id)
        deducao_existente = session.query(deducao).filter_by(
            espessura_id=espessura_obj.id,
            canal_id=canal_obj.id,
            material_id=material_obj.id,
            valor=nova_deducao_valor
        ).first()

        if not deducao_existente:
            nova_deducao = deducao(
                espessura_id=espessura_obj.id,
                canal_id=canal_obj.id,
                material_id=material_obj.id,
                valor=nova_deducao_valor,
                obs_id=nova_observacao.id if nova_observacao else None  # Associa a observação à dedução se existir
            )
            session.add(nova_deducao)
            session.commit()
            aviso_label.config(text="Nova dedução adicionada com sucesso!", fg="green")
        else:
            aviso_label.config(text="Dedução já existe no banco de dados.", fg="red")

        deducao_espessura_combobox.set('')
        deducao_canal_combobox.set('')
        deducao_material_combobox.set('')
        deducao_valor_entry.delete(0, tk.END)
        deducao_obs_entry.delete(0, tk.END)

    def adicionar_dados():
        aviso_label.config(text="", fg="red")  # Limpar aviso anterior
        # Adicionar novos valores ao banco de dados apenas se os campos estiverem preenchidos
        if material_nome_entry.get() or material_densidade_entry.get():
            nome_material = material_nome_entry.get()
            densidade_material = float(material_densidade_entry.get())
            material_existente = session.query(material).filter_by(nome=nome_material).first()
            if not material_existente:
                novo_material = material(nome=nome_material, densidade=densidade_material)
                session.add(novo_material)
                material_nome_entry.delete(0, tk.END)
                material_densidade_entry.delete(0, tk.END)
                aviso_label.config(text="Novo material adicionado com sucesso!", fg="green")
            else:
                aviso_label.config(text="Material já existe no banco de dados.", fg="red")

        if espessura_valor_entry.get():
            valor_espessura = float(espessura_valor_entry.get().replace(',', '.'))
            espessura_existente = session.query(espessura).filter_by(valor=valor_espessura).first()
            if not espessura_existente:
                nova_espessura = espessura(valor=valor_espessura)
                session.add(nova_espessura)
                espessura_valor_entry.delete(0, tk.END)
                aviso_label.config(text="Nova espessura adicionada com sucesso!", fg="green")
            else:
                aviso_label.config(text="Espessura já existe no banco de dados.", fg="red")

        if canal_valor_entry.get():
            valor_canal = float(canal_valor_entry.get())
            canal_existente = session.query(canal).filter_by(valor=valor_canal).first()
            if not canal_existente:
                novo_canal = canal(valor=valor_canal)
                session.add(novo_canal)
                canal_valor_entry.delete(0, tk.END)
                aviso_label.config(text="Novo canal adicionado com sucesso!", fg="green")
            else:
                aviso_label.config(text="Canal já existe no banco de dados.", fg="red")

        session.commit()
        atualizar_dados()

    def atualizar_dados():
        # Atualizar valores dos comboboxes
        materiais = [m.nome for m in session.query(material).all()]
        espessuras = [e.valor for e in session.query(espessura).all()]
        canais = [c.valor for c in session.query(canal).all()]

        deducao_material_combobox['values'] = materiais
        deducao_espessura_combobox['values'] = espessuras
        deducao_canal_combobox['values'] = canais
    
    def on_closing():
            root_app.destroy()
            root.destroy()
            app.main()

    root = tk.Tk()
    root.title("Tabela de dobra")
    root.geometry("500x260")
    root.resizable(False, False)

    # Centralizar a janela add_form em relação à janela principal
    root_app.update_idletasks()
    x = root_app.winfo_x() + (root_app.winfo_width() // 2) - (500 // 2)
    y = root_app.winfo_y() + (root_app.winfo_height() // 2) - (260 // 2)
    root.geometry(f"+{x}+{y}")

    label1 = tk.Label(root, text="Adicionar Nova Dedução de Dobra", font=("Helvetica", 16))
    label1.pack(pady=5)

    # Frame principal para organizar as colunas
    main_frame = tk.Frame(root)
    main_frame.pack(pady=5)

    tk.Label(main_frame, text="Material:").grid(row=0, column=0)
    deducao_material_combobox = ttk.Combobox(main_frame, values=[m.nome for m in session.query(material).all()])
    deducao_material_combobox.grid(row=0, column=1)
    
    tk.Label(main_frame, text="Espessura:").grid(row=1, column=0)
    deducao_espessura_combobox = ttk.Combobox(main_frame, values=[m.valor for m in session.query(espessura).all()])
    deducao_espessura_combobox.grid(row=1, column=1)

    tk.Label(main_frame, text="Canal:").grid(row=2, column=0)
    deducao_canal_combobox = ttk.Combobox(main_frame, values=[c.valor for c in session.query(canal).all()])
    deducao_canal_combobox.grid(row=2, column=1)

    tk.Label(main_frame, text="Dedução:").grid(row=3, column=0)
    deducao_valor_entry = tk.Entry(main_frame)
    deducao_valor_entry.grid(row=3, column=1)

    tk.Label(main_frame, text="observação:").grid(row=4, column=0)
    deducao_obs_entry = tk.Entry(main_frame)
    deducao_obs_entry.grid(row=4, column=1)

    tk.Button(main_frame, text="Adicionar Dedução", command=adicionar_deducao_e_observacao).grid(row=5,column=0, columnspan=2, pady=5)

    tk.Label(main_frame, text="Material:").grid(row=0, column=3)
    material_nome_entry = tk.Entry(main_frame)
    material_nome_entry.grid(row=0, column=4)

    tk.Label(main_frame, text="Densidade:").grid(row=1, column=3)
    material_densidade_entry = tk.Entry(main_frame)
    material_densidade_entry.grid(row=1, column=4)

    tk.Label(main_frame, text="Espessura:").grid(row=2, column=3)
    espessura_valor_entry = tk.Entry(main_frame)
    espessura_valor_entry.grid(row=2, column=4)

    tk.Label(main_frame, text="Canal:").grid(row=3, column=3)
    canal_valor_entry = tk.Entry(main_frame)
    canal_valor_entry.grid(row=3, column=4)

    tk.Button(main_frame, text="Adicionar Dados", command=adicionar_dados).grid(row=4, column=4, pady=5)
   
    aviso_label = tk.Label(root, text="", font=("Helvetica", 10))
    aviso_label.pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main(None)