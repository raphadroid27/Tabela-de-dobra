import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from aba2 import criar_aba2

def main():
    
    # Configuração do banco de dados
    engine = create_engine('sqlite:///tabela_de_dobra.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    root = tk.Tk()
    root.title("Tabela de dobra")
    root.geometry("600x400")

   # Criando o Notebook (abas)
    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, expand=True)

    # Criando os frames para as abas
    aba1 = ttk.Frame(notebook, width=400, height=400)
    aba1.pack(fill='both', expand=True)

    # Adicionando as abas ao Notebook
    notebook.add(aba1, text='Aba 1')
    criar_aba2(notebook)

    # Conteúdo da Aba 1
    label1 = tk.Label(aba1, text="Bem-vindo à Tabela de Dobra")
    label1.pack(pady=10)

    frame = tk.Frame(aba1)
    frame.pack(padx=10, pady=10)

    # Lista de espessuras
    espessuras_valores = [str(e.valor) for e in session.query(espessura).all()]

    espessura_label = tk.Label(frame, text="Espessura: ")
    espessura_label.grid(row=0, column=0)
    
    espessura_combobox = ttk.Combobox(frame, values=espessuras_valores)
    espessura_combobox.grid(row=1, column=0, padx=10)

    #lista de materiais

    materiais_nomes = [m.nome for m in session.query(material).all()]

    material_label = tk.Label(frame, text="Material:")
    material_label.grid(row=0, column=1)

    material_combobox = ttk.Combobox(frame, values=materiais_nomes)
    material_combobox.grid(row=1, column=1,padx=10)

    #lista de canais
    canais_valores = [str(c.valor) for c in session.query(canal).all()]

    canal_label = tk.Label(frame, text="Canal:")
    canal_label.grid(row=0, column=2)

    canal_combobox = ttk.Combobox(frame, values=canais_valores)
    canal_combobox.grid(row=1, column=2,padx=10)

    # Label para exibir a dedução
    deducao_label = tk.Label(frame, text="Dedução: ")
    deducao_label.grid(row=3, column=1,padx=10)

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