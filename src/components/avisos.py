"""
Módulo responsável por criar o frame de avisos na interface gráfica.
"""

import tkinter as tk


class InterfaceAvisos:
    """
    Classe para criar o frame de avisos na interface gráfica.
    Esta classe segue o padrão das outras classes UI do aplicativo.
    """

    def __init__(self, root):
        """
        Inicializa o frame de avisos.

        Args:
            root: O widget pai onde o frame será inserido.
        """
        self.frame = tk.Frame(root)
        self.criar_avisos()

    def criar_avisos(self):
        """
        Cria os labels de avisos dentro do frame.
        """
        avisos_textos = [
            "1. Xadrez → Laser sempre corta com a face xadrez para Baixo ↓.",
            "2. Corrugado → Laser sempre corta com a face do corrugado para Cima ↑.",
            "3. Ferramenta 'bigode': fazer alívio de dobra em abas maiores que 20mm.",
        ]

        for i, aviso in enumerate(avisos_textos):
            aviso_label = tk.Label(
                self.frame,
                text=aviso,
                anchor="w",
                font=("Arial", 10),
                wraplength=300,
                justify="left",
            )
            aviso_label.grid(row=i, column=0, sticky="w", padx=5, pady=2)


# Função de compatibilidade com o código existente
def avisos(root):
    """
    Função de compatibilidade que cria uma instância de InterfaceAvisos.

    Args:
        root: O widget pai onde o frame será inserido.

    Returns:
        InterfaceAvisos: Instância da classe InterfaceAvisos.
    """
    return InterfaceAvisos(root)
