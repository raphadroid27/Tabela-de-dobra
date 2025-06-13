"""
# Formulário de Espessura
# Este módulo implementa a interface gráfica para gerenciar espessuras de materiais.
# Ele permite adicionar, editar e excluir registros de espessuras, utilizando a
# biblioteca tkinter para a construção da interface. As variáveis globais são
# gerenciadas pelo módulo `globals`, enquanto as operações de banco de dados
# são realizadas pelo módulo `funcoes`.
"""

import tkinter as tk
from tkinter import ttk

from src.utils.janelas import no_topo, posicionar_janela
from src.utils.interface import (
    listar,
    limpar_busca,
    configurar_main_frame,
    configurar_frame_edicoes,
)
from src.utils.utilitarios import obter_caminho_icone
from src.utils.operacoes_crud import buscar, preencher_campos, excluir, editar, adicionar


class FormEspessura:
    """Classe do formulário de espessuras."""

    def __init__(self, root, app_principal):
        """
        Configura a janela principal do formulário de espessuras.
        """
        self.espessura_form = tk.Toplevel(root)
        self.espessura_form.geometry("240x280")
        self.espessura_form.resizable(False, False)

        icone_path = obter_caminho_icone()
        self.espessura_form.iconbitmap(icone_path)

        no_topo(self.espessura_form, app_principal)
        posicionar_janela(self.espessura_form, app_principal, None)

    def criar_frame_busca(self, app_principal):
        """
        Cria o frame de busca.
        """
        frame_busca = tk.LabelFrame(self.frame, text="Buscar Espessuras", pady=5)
        frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        for i in range(3):
            frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

        tk.Label(frame_busca, text="Valor:").grid(row=0, column=0)
        self.espessura_busca_entry = tk.Entry(frame_busca)
        self.espessura_busca_entry.grid(row=0, column=1, sticky="ew")
        self.espessura_busca_entry.bind("<KeyRelease>", lambda event: buscar("espessura", self))

        tk.Button(frame_busca, text="Limpar", command=lambda: limpar_busca("espessura", self)).grid(
            row=0, column=2, padx=5, pady=5
        )

    def criar_lista_espessuras(self, app_principal):
        """
        Cria a lista de espessuras.
        """
        columns = ("Id", "Valor")
        self.espessura_lista = ttk.Treeview(self.frame, columns=columns, show="headings")
        self.espessura_lista["displaycolumns"] = "Valor"
        for col in columns:
            self.espessura_lista.heading(col, text=col)
            self.espessura_lista.column(col, anchor="center")

        self.espessura_lista.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        listar("espessura", ui=self)

    def criar_frame_edicoes(self, app_principal):
        """
        Cria o frame de edições.
        """
        frame_edicoes = configurar_frame_edicoes(
            self.frame,
            text=(
                "Adicionar Espessura" if not app_principal.editar_espessura else "Editar Espessura"
            ),
        )

        tk.Label(frame_edicoes, text="Valor:").grid(row=0, column=0, sticky="w", padx=5)
        self.espessura_valor_entry = tk.Entry(frame_edicoes)
        self.espessura_valor_entry.grid(row=0, column=1, sticky="ew")

        return frame_edicoes

    def configurar_botoes(self, frame_edicoes, app_principal):
        """
        Configura os botões de ação (Adicionar, Atualizar, Excluir).
        """
        if app_principal.editar_espessura:
            if self.espessura_form:
                self.espessura_form.title("Editar/Excluir Espessura")
            if self.espessura_lista:
                self.espessura_lista.bind(
                    "<ButtonRelease-1>", lambda event: preencher_campos("espessura", self)
                )
            frame_edicoes.config(text="Editar Espessura")

            tk.Button(
                frame_edicoes,
                text="Atualizar",
                command=lambda: editar("espessura", self, app_principal),
                bg="green",
            ).grid(row=0, column=2, padx=5, pady=5, sticky="e")

            tk.Button(
                self.frame,
                text="Excluir",
                command=lambda: excluir("espessura", self, app_principal),
                bg="red",
            ).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        else:
            if self.espessura_form:
                self.espessura_form.title("Adicionar Espessura")
            frame_edicoes.config(text="Adicionar Espessura")

            tk.Button(
                frame_edicoes,
                text="Adicionar",
                command=lambda: adicionar("espessura", self, app_principal),
                bg="cyan",
            ).grid(row=0, column=2, padx=5, pady=5, sticky="e")

    def main(self, root, app_principal):
        """
        Inicializa e exibe o formulário de gerenciamento de espessuras.
        """
        self.frame = configurar_main_frame(self.espessura_form)
        self.criar_frame_busca(app_principal)
        frame_edicoes = self.criar_frame_edicoes(app_principal)
        self.criar_lista_espessuras(app_principal)
        self.configurar_botoes(frame_edicoes, app_principal)


def main(root):
    """
    Função principal para inicializar o formulário de espessuras.
    """
    # Importar app para acessar a instância principal
    from src.app import app

    form = FormEspessura(root, app_principal=app)
    form.main(root, app)


if __name__ == "__main__":
    main(None)
