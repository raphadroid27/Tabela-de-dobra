import tkinter as tk
from tkinter import ttk
from models import espessura, material, canal, deducao
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from aba2 import criar_aba2
from aba1 import criar_aba1

def main():

    root = tk.Tk()
    root.title("Tabela de dobra")
    root.geometry("600x400")
    

    label1 = tk.Label(root, text="Bem-vindo à Tabela de Dobra", font=("Helvetica", 16))
    label1.pack(pady=10)

   # Criando o Notebook (abas)
    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, expand=True)

    criar_aba1(notebook)
    criar_aba2(notebook)
    
    root.mainloop()

if __name__ == "__main__":
    main()