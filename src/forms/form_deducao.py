'''
# Formulário de Dedução
# Este módulo implementa o formulário de dedução, permitindo a adição, edição
# e exclusão de deduções. Ele utiliza a biblioteca tkinter para a interface
# gráfica, o módulo globals para variáveis globais e o módulo funcoes para
# operações relacionadas ao banco de dados.
'''
import tkinter as tk
from tkinter import ttk
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.interface import (listar,
                                 limpar_busca,
                                 atualizar_widgets,
                                 configurar_main_frame,
                                 configurar_frame_edicoes
                                 )
from src.utils.utilitarios import obter_caminho_icone
from src.utils.operacoes_crud import (buscar,
                                      preencher_campos,
                                      excluir,
                                      editar,
                                      adicionar
                                      )
from src.config import globals as g

class FormDeducao:

    def __init__(self, root, app_principal):
        '''
        Configura a janela principal do formulário de deduções.
        '''
        self.deducao_form = tk.Toplevel(root)
        self.deducao_form.geometry("500x420")
        self.deducao_form.resizable(False, False)

        icone_path = obter_caminho_icone()
        self.deducao_form.iconbitmap(icone_path)

        no_topo(self.deducao_form)
        #posicionar_janela(self.deducao_form, None, app_principal)

    def criar_frame_busca(self, app_principal):
        '''
        Cria o frame de busca.
        '''
        frame_busca = tk.LabelFrame(self.frame, text='Buscar Deduções', pady=5)
        frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        for i in range(4):
            frame_busca.columnconfigure(i, weight=1)

        tk.Label(frame_busca, text="Material:").grid(row=0, column=0, padx=2, sticky='sw')
        self.deducao_material_combo = ttk.Combobox(frame_busca)
        self.deducao_material_combo.grid(row=1, column=0, padx=5, sticky="ew")
        self.deducao_material_combo.bind("<<ComboboxSelected>>", lambda event: buscar('dedução', self))

        tk.Label(frame_busca, text="Espessura:").grid(row=0, column=1, padx=2, sticky='sw')
        self.deducao_espessura_combo = ttk.Combobox(frame_busca)
        self.deducao_espessura_combo.grid(row=1, column=1, padx=5, sticky="ew")
        self.deducao_espessura_combo.bind("<<ComboboxSelected>>", lambda event: buscar('dedução', self))

        tk.Label(frame_busca, text="Canal:").grid(row=0, column=2, padx=2, sticky='sw')
        self.deducao_canal_combo = ttk.Combobox(frame_busca)
        self.deducao_canal_combo.grid(row=1, column=2, padx=5, sticky="ew")
        self.deducao_canal_combo.bind("<<ComboboxSelected>>", lambda event: buscar('dedução', self))

        tk.Button(frame_busca,
                text="Limpar",
                width=10,
                command=lambda: limpar_busca('dedução', self)).grid(row=1, column=3, padx=5, pady=5)

    def criar_lista_deducoes(self, app_principal):
        '''
        Cria a lista de deduções.
        '''
        columns = ("Id", "Material", "Espessura", "Canal", "Dedução", "Observação", "Força")
        self.deducao_lista = ttk.Treeview(self.frame, columns=columns, show="headings")
        self.deducao_lista["displaycolumns"] = ("Material",
                                        "Espessura",
                                        "Canal",
                                        "Dedução",
                                        "Observação",
                                        "Força"
                                        )
        for col in columns:
            self.deducao_lista.heading(col, text=col)
            self.deducao_lista.column(col, anchor="center", width=60)
            self.deducao_lista.column("Material", width=80)
            self.deducao_lista.column("Observação", width=120, anchor="w")

        self.deducao_lista.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        listar('dedução', ui=self)

    def criar_frame_edicoes(self, app_principal):
        '''
        Cria o frame de edições.
        '''
        frame_edicoes = configurar_frame_edicoes(self.frame,
                                                text='Nova Dedução'
                                                if not app_principal.editar_deducao
                                                else 'Editar Dedução'
                                                )

        tk.Label(frame_edicoes, text="Valor:").grid(row=0, column=0, padx=2, sticky='sw')
        self.deducao_valor_entry = tk.Entry(frame_edicoes)
        self.deducao_valor_entry.grid(row=1, column=0, padx=5, sticky="ew")

        tk.Label(frame_edicoes, text="Observação:").grid(row=0, column=1, padx=2, sticky='sw')
        self.deducao_observacao_entry = tk.Entry(frame_edicoes)
        self.deducao_observacao_entry.grid(row=1, column=1, padx=5, sticky="ew")

        tk.Label(frame_edicoes, text="Força:").grid(row=0, column=2, padx=2, sticky='sw')
        self.deducao_forca_entry = tk.Entry(frame_edicoes)
        self.deducao_forca_entry.grid(row=1, column=2, padx=5, sticky="ew")

        return frame_edicoes

    def configurar_botoes(self, frame_edicoes, app_principal):
        '''
        Configura os botões de ação (Adicionar, Atualizar, Excluir).
        '''
        if app_principal.editar_deducao:
            if self.deducao_form:
                self.deducao_form.title("Editar/Excluir Dedução")
            if self.deducao_lista:
                self.deducao_lista.bind("<ButtonRelease-1>", lambda event: preencher_campos('dedução', self))
            frame_edicoes.config(text='Editar Dedução')

            tk.Button(
                frame_edicoes,
                text="Atualizar",
                bg="green",
                width=10,
                command=lambda: editar('dedução', self)
            ).grid(
                row=1,
                column=3,
                padx=5,
                pady=5,
                sticky="eW"
            )

            tk.Button(
                self.frame,
                text="Excluir",
                bg="red",
                width=10,
                command=lambda: excluir('dedução', self)
            ).grid(
                row=2,
                column=0,
                padx=5,
                pady=5,
                sticky="e"
            )
        else:
            if self.deducao_form:
                self.deducao_form.title("Adicionar Dedução")
            frame_edicoes.config(text='Nova Dedução')

            tk.Button(
                frame_edicoes,
                text="Adicionar",
                bg="cyan",
                width=10,
                command=lambda: adicionar('dedução', self)
            ).grid(
                row=1,
                column=3,
                padx=5,
                pady=5,
                sticky="eW"
            )

    def atualizar_comboboxes(self, cabecalho_ui):
        '''
        Atualiza os widgets de combobox.
        '''
        tipos = ['material', 'espessura', 'canal']
        for tipo in tipos:
            atualizar_widgets(cabecalho_ui, form_ui=self, tipo=tipo)

    def main(self, root, app_principal):
        '''
        Inicializa e exibe o formulário de gerenciamento de deduções.
        '''
        #self.configurar_janela(root)
        self.frame = configurar_main_frame(self.deducao_form)
        self.criar_frame_busca(app_principal)
        frame_edicoes = self.criar_frame_edicoes(app_principal)  # Criar ANTES da lista
        self.criar_lista_deducoes(app_principal)  # Criar DEPOIS do frame de edições
        self.configurar_botoes(frame_edicoes, app_principal)
        self.atualizar_comboboxes(cabecalho_ui=app_principal.cabecalho_ui)

def main(root):
    '''
    Função principal para inicializar o formulário de deduções.
    '''
    # Importar app para acessar a instância principal
    from src.app import app
    form = FormDeducao(root, app_principal=app)
    form.main(root, app)
