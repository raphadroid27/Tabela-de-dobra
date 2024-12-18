import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

def main():
    
    # Configuração do banco de dados
    engine = create_engine('sqlite:///tabela_de_dobra.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    root = tk.Tk()
    root.title("Tabela de dobra")
    root.geometry("400x400")

    # Adicionando um Label
    label = tk.Label(root, text="Bem-vindo à Tabela de Dobra")
    label.pack(pady=10)

    frame = tk.Frame(root)
    frame.grid(row=0, column=0, padx=10, pady=10)

    # Lista de espessuras
    espessuras_valores = [str(e.valor) for e in session.query(espessura).all()]
    espessura_combobox = ttk.Combobox(root, values=espessuras_valores)
    espessura_combobox.pack(pady=10)

    #lista de materiais
    materiais_nomes = [m.nome for m in session.query(material).all()]
    material_combobox = ttk.Combobox(root, values=materiais_nomes)
    material_combobox.pack(pady=10)

    #lista de canais
    canais_valores = [str(c.valor) for c in session.query(canal).all()]
    canal_combobox = ttk.Combobox(root, values=canais_valores)
    canal_combobox.pack(pady=10)

    # Label para exibir a dedução
    deducao_label = tk.Label(root, text="Dedução: ")
    deducao_label.pack(pady=10)

    def atualizar_deducao():
        espessura_valor = float(espessura_combobox.get())
        material_nome = material_combobox.get()
        canal_valor = float(canal_combobox.get())

        deducao_obj = session.query(deducao).join(espessura).join(material).join(canal).filter(
            espessura.valor == espessura_valor,
            material.nome == material_nome,
            canal.valor == canal_valor
        ).first()

        if deducao_obj:
            deducao_label.config(text=f"Dedução: {deducao_obj.valor}")
        else:
            deducao_label.config(text="Dedução: Não encontrada")

    # Botão para atualizar a dedução
    button = tk.Button(root, text="Atualizar Dedução", command=atualizar_deducao)
    button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()