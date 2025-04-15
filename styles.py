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
import darkdetect
import globals as g

def configurar_estilos():
    """
    Configura os estilos para os widgets do aplicativo.
    """
    style = ttk.Style()
    style.theme_use('clam')

    # Detectar tema do sistema operacional
    tema_escuro = darkdetect.isDark() == True

    if tema_escuro:
        # Configurações para tema escuro
        g.PRINC_FORM.configure(background="#2e2e2e")  # Adicionando configuração de fundo
        style.configure("TLabel", background="#2e2e2e", foreground="#ffffff")
        style.configure("Titulo.TLabel", background="#2e2e2e", foreground="#ffffff")
        style.configure("Campo.TLabel", background="#2e2e2e", foreground="#ffffff")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabelframe", background="#2e2e2e", foreground="#ffffff")
        style.configure("TEntry", background="#3c3c3c", foreground="#ffffff", fieldbackground="#3c3c3c")
        style.configure("TButton", background="#444444", foreground="#ffffff")
        style.configure("Treeview", background="#3c3c3c", foreground="#ffffff", fieldbackground="#3c3c3c")
        style.configure("Treeview.Heading", background="#444444", foreground="#ffffff")
    else:
        # Configurações para tema claro
        g.PRINC_FORM.configure(background="#f0f0f0")  # Adicionando configuração de fundo
        style.configure("TLabel", background="#f0f0f0", foreground="#000000")
        style.configure("Titulo.TLabel", background="#f0f0f0", foreground="#000000")
        style.configure("Campo.TLabel", background="#f0f0f0", foreground="#000000")
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabelframe", background="#f0f0f0", foreground="#000000")
        style.configure("TEntry", background="#ffffff", foreground="#000000", fieldbackground="#ffffff")
        style.configure("TButton", background="#e0e0e0", foreground="#000000")
        style.configure("Treeview", background="#f0f0f0", foreground="#000000", fieldbackground="#f0f0f0")
        style.configure("Treeview.Heading", background="#e0e0e0", foreground="#000000")

    # Estilos gerais
    style.configure("Titulo.TLabel",
                    font=("Arial", 10, 'bold'),
                    )
    
    style.configure("Campo.TLabel",
                    font=("Arial", 10),
                    relief="sunken"
                    )
    
    style.configure("TEntry",
                    font=("Arial", 10),
                    )
    
    style.configure("TLabelframe",
                    borderwidth=2,
                    relief="groove",
                    )
    
    style.configure("TLabelframe.Label",
                    font=("Arial", 10, "bold"),
                    foreground="#007ACC",
                    background="#f0f0f0")

    # Botão Geral
    style.configure("TButton",
                    font=("Arial", 10, "bold"),
                    width=10)

    # Botão Excluir
    style.configure("Excluir.TButton",
                        font=("Arial", 10, "bold"),
                        foreground="white",
                        background="#cc0000",
                        width=10
                        )
    style.map("Excluir.TButton",
            background=[("active", "#990000"), ("!disabled", "#cc0000")],
            )


    # Botão Editar
    style.configure("Atualizar.TButton",
                    font=("Arial", 10, "bold"),
                    foreground="white",
                    background="#ffa900",
                    width=10
                    )
    style.map("Atualizar.TButton",
              background=[("active", "#cc8a00"), ("!disabled", "#ffa900")],
              )


    # Botão Adicionar
    style.configure("Adicionar.TButton",
                    font=("Arial", 10, "bold"),
                    foreground="white",
                    width=10)
    style.map("Adicionar.TButton",
              background=[("!disabled", "#008000"), ("active", "#005A00")]
              )


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