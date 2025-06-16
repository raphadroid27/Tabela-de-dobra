"""
# Formulário de Material
# Este módulo contém a implementação do formulário de materiais, que permite
# adicionar, editar e excluir materiais. O formulário é
# construído usando a biblioteca tkinter e utiliza o módulo globals para
# armazenar variáveis globais e o módulo funcoes para realizar operações
# relacionadas ao banco de dados.
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


class FormMaterial:
    """Classe do formulário de materiais."""

    def __init__(self, root, app_principal):
        """
        Configura a janela principal do formulário de materiais.
        """
        self.material_form = tk.Toplevel(root)
        self.material_form.geometry("340x420")
        self.material_form.resizable(False, False)

        icone_path = obter_caminho_icone()
        self.material_form.iconbitmap(icone_path)

        no_topo(self.material_form, app_principal)
        posicionar_janela(self.material_form, app_principal, None)

    def criar_frame_busca(self, app_principal):
        """
        Cria o frame de busca.
        """
        frame_busca = tk.LabelFrame(self.frame, text="Buscar Materiais", pady=5)
        frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        for i in range(3):
            frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

        tk.Label(frame_busca, text="Nome:").grid(row=0, column=0)
        self.material_busca_entry = tk.Entry(frame_busca)
        self.material_busca_entry.grid(row=0, column=1, sticky="ew")
        self.material_busca_entry.bind("<KeyRelease>", lambda event: buscar("material", self))

        tk.Button(frame_busca, text="Limpar", command=lambda: limpar_busca("material", self)).grid(
            row=0, column=2, padx=5, pady=5
        )

    def criar_lista_materiais(self, app_principal):
        """
        Cria a lista de materiais.
        """
        columns = ("Id", "Nome", "Densidade", "Escoamento", "Elasticidade")
        self.material_lista = ttk.Treeview(self.frame, columns=columns, show="headings")
        self.material_lista["displaycolumns"] = ("Nome", "Densidade", "Escoamento", "Elasticidade")
        for col in columns:
            self.material_lista.heading(col, text=col)
            self.material_lista.column(col, anchor="center", width=20)

        self.material_lista.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        listar("material", ui=self)

    def criar_frame_edicoes(self, app_principal):
        """
        Cria o frame de edições.
        """
        frame_edicoes = configurar_frame_edicoes(
            self.frame,
            text="Novo Material" if not app_principal.editar_material else "Editar Material",
        )

        tk.Label(frame_edicoes, text="Nome:", anchor="w").grid(row=0, column=0, padx=2, sticky="sw")
        self.material_nome_entry = tk.Entry(frame_edicoes)
        self.material_nome_entry.grid(row=1, column=0, padx=5, sticky="ew")

        tk.Label(frame_edicoes, text="Densidade:", anchor="w").grid(
            row=0, column=1, padx=2, sticky="sw"
        )
        self.material_densidade_entry = tk.Entry(frame_edicoes)
        self.material_densidade_entry.grid(row=1, column=1, padx=5, sticky="ew")

        tk.Label(frame_edicoes, text="Escoamento:", anchor="w").grid(
            row=2, column=0, padx=2, sticky="sw"
        )
        self.material_escoamento_entry = tk.Entry(frame_edicoes)
        self.material_escoamento_entry.grid(row=3, column=0, padx=5, sticky="ew")

        tk.Label(frame_edicoes, text="Elasticidade:", anchor="w").grid(
            row=2, column=1, padx=2, sticky="sw"
        )
        self.material_elasticidade_entry = tk.Entry(frame_edicoes)
        self.material_elasticidade_entry.grid(row=3, column=1, padx=5, sticky="ew")

        return frame_edicoes

    def configurar_botoes(self, frame_edicoes, app_principal):
        """
        Configura os botões de ação (Adicionar, Atualizar, Excluir).
        """
        if app_principal.editar_material:
            if self.material_form:
                self.material_form.title("Editar/Excluir Material")
            if self.material_lista:
                self.material_lista.bind(
                    "<ButtonRelease-1>", lambda event: preencher_campos("material", self)
                )
            frame_edicoes.config(text="Editar Material")

            tk.Button(
                self.frame,
                text="Excluir",
                command=lambda: excluir("material", self, app_principal),
                bg="red",
            ).grid(row=2, column=0, padx=5, pady=5, sticky="e")

            tk.Button(
                frame_edicoes,
                text="Atualizar",
                command=lambda: editar("material", self, app_principal),
                bg="green",
            ).grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=3)
        else:
            if self.material_form:
                self.material_form.title("Adicionar Material")
            frame_edicoes.config(text="Novo Material")
            tk.Button(
                frame_edicoes,
                text="Adicionar",
                command=lambda: adicionar("material", self, app_principal),
                bg="cyan",
            ).grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=3)

    def main(self, root, app_principal):
        """
        Inicializa e exibe o formulário de gerenciamento de materiais.
        """
        self.frame = configurar_main_frame(self.material_form)
        self.criar_frame_busca(app_principal)
        frame_edicoes = self.criar_frame_edicoes(app_principal)
        self.criar_lista_materiais(app_principal)
        self.configurar_botoes(frame_edicoes, app_principal)


def main(root):
    """
    Função principal para inicializar o formulário de materiais.
    """
    # Importar app para acessar a instância principal
    from src.app import APP

    form = FormMaterial(root, app_principal=APP)
    form.main(root, APP)


if __name__ == "__main__":
    main(None)
