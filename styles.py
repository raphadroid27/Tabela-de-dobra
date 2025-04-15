"""
styles.py
Este módulo contém a configuração de estilos para os widgets do aplicativo.
Utiliza a biblioteca tkinter para criar uma interface gráfica personalizada.

Os estilos são aplicados a diferentes tipos de widgets, como botões, entradas, rótulos e tabelas.
Incluem configurações de fonte, cores, tamanhos e comportamentos de interação.

Objetivo:
- Melhorar a aparência visual do aplicativo.
- Proporcionar uma experiência de usuário mais consistente e intuitiva.
"""

from tkinter import ttk

def configurar_estilos():
    """
    Configura os estilos para os widgets do aplicativo.
    """
    style = ttk.Style()
    style.theme_use('clam')

    # Estilos gerais
    style.configure("TLabel", font=("Arial", 10))
    style.configure("TEntry", font=("Arial", 10))

    # Botão Geral
    style.configure("TButton",
                    font=("Arial", 10, "bold"),
                    foreground="black",
                    width=10)

    # Botão Excluir
    style.configure("Excluir.TButton", 
                    font=("Arial", 10, "bold"),
                    foreground="white",
                    background="red",
                    width=10,
                    bordercolor="red",
                    focuscolor="red")
    style.map("Excluir.TButton",
              background=[("active", "#CC0000"), ("!disabled", "red")],
              relief=[("pressed", "sunken"), ("!pressed", "raised")])

    # Botão Editar
    style.configure("Editar.TButton",
                    font=("Arial", 10, "bold"),
                    foreground="white",
                    width=10,
                    background="#FFA500",)


    # Botão Adicionar
    style.configure("Adicionar.TButton",
                    font=("Arial", 10, "bold"),
                    foreground="white",
                    width=10,
                    background="#008000",
                    bordercolor="#008000")
    style.map("Adicionar.TButton",
              background=[("!disabled", "#008000"), ("active", "#005A00")],
              relief=[("pressed", "sunken"), ("!pressed", "raised")])


    style.configure("Salvar.TButton",
                    font=("Arial", 10, "bold"),
                    foreground="white",
                    width=10,
                    background="#007ACC",
                    bordercolor="#007ACC")
    style.map("Salvar.TButton",
              background=[("!disabled", "#007ACC"), ("active", "#005A9C")],
              relief=[("pressed", "sunken"), ("!pressed", "raised")])

    # Treeview
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#007ACC", foreground="black")
    style.configure("Treeview", font=("Arial", 10), rowheight=24, background="#f0f0f0", fieldbackground="#f0f0f0")
    style.map("Treeview", background=[("selected", "#007ACC")])