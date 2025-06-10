'''
# Formulário de Canal
# Este módulo implementa o formulário de canal, permitindo a adição, edição
# e exclusão de canais. Ele utiliza a biblioteca tkinter para a interface
# gráfica, o módulo globals para variáveis globais e o módulo funcoes para
# operações relacionadas ao banco de dados.
'''
import tkinter as tk
from tkinter import ttk
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.interface import (listar,
                                 limpar_busca,
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

class FormCanal:

    def __init__(self, root, app_principal):
        '''
        Configura a janela principal do formulário de canais.
        '''
        self.canal_form = tk.Toplevel(root)
        self.canal_form.geometry("340x420")
        self.canal_form.resizable(False, False)

        icone_path = obter_caminho_icone()
        self.canal_form.iconbitmap(icone_path)

        no_topo(self.canal_form, app_principal)
        posicionar_janela(self.canal_form, app_principal, None)

    def criar_frame_busca(self, app_principal):
        '''
        Cria o frame de busca.
        '''
        frame_busca = tk.LabelFrame(self.frame, text='Buscar Canais', pady=5)
        frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        for i in range(3):
            frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

        tk.Label(frame_busca, text="Valor:").grid(row=0, column=0)
        self.canal_busca_entry = tk.Entry(frame_busca)
        self.canal_busca_entry.grid(row=0, column=1, sticky="ew")
        self.canal_busca_entry.bind("<KeyRelease>", lambda event: buscar('canal', self))

        tk.Button(frame_busca, text="Limpar",
                  command=lambda: limpar_busca('canal', self)).grid(row=0, column=2, padx=5, pady=5)

    def criar_lista_canais(self, app_principal):
        '''
        Cria a lista de canais.
        '''
        columns = ("Id", "Canal", "Largura", "Altura", "Compr.", "Obs.")
        self.canal_lista = ttk.Treeview(self.frame, columns=columns, show="headings")
        self.canal_lista["displaycolumns"] = ("Canal", "Largura", "Altura", "Compr.", "Obs.")
        for col in columns:
            self.canal_lista.heading(col, text=col)
            self.canal_lista.column(col, anchor="center", width=20)

        self.canal_lista.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        listar('canal', ui=self)

    def criar_frame_edicoes(self, app_principal):
        '''
        Cria o frame de edições.
        '''
        frame_edicoes = configurar_frame_edicoes(self.frame,
                                                 text='Novo Canal'
                                                 if not app_principal.editar_canal
                                                 else 'Editar Canal'
                                                 )

        tk.Label(frame_edicoes, text="Valor:", anchor="w").grid(row=0, column=0, padx=2, sticky='sw')
        self.canal_valor_entry = tk.Entry(frame_edicoes)
        self.canal_valor_entry.grid(row=1, column=0, padx=5, sticky="ew")

        tk.Label(frame_edicoes, text="Largura:", anchor="w").grid(row=0, padx=2, column=1, sticky='sw')
        self.canal_largura_entry = tk.Entry(frame_edicoes)
        self.canal_largura_entry.grid(row=1, column=1, padx=5, sticky="ew")

        tk.Label(frame_edicoes, text="Altura:", anchor="w").grid(row=2, column=0, padx=2, sticky='sw')
        self.canal_altura_entry = tk.Entry(frame_edicoes)
        self.canal_altura_entry.grid(row=3, column=0, padx=5, sticky="ew")

        tk.Label(frame_edicoes,
                 text="Comprimento total:",
                 anchor="w").grid(row=2, column=1, padx=2, sticky='sw')

        self.canal_comprimento_entry = tk.Entry(frame_edicoes)
        self.canal_comprimento_entry.grid(row=3, column=1, padx=5, sticky="ew")

        tk.Label(frame_edicoes,
                 text="Observação:",
                 anchor="w").grid(row=4, column=0, padx=2, sticky='sw')

        self.canal_observacao_entry = tk.Entry(frame_edicoes)
        self.canal_observacao_entry.grid(row=5, column=0, columnspan=2, padx=5, sticky="ew")

        return frame_edicoes

    def configurar_botoes(self, frame_edicoes, app_principal):
        '''
        Configura os botões de ação (Adicionar, Atualizar, Excluir).
        '''
        if app_principal.editar_canal:
            if self.canal_form:
                self.canal_form.title("Editar/Excluir Canal")
            if self.canal_lista:
                self.canal_lista.bind("<ButtonRelease-1>", lambda event: preencher_campos('canal', self))
            frame_edicoes.config(text='Editar Canal')

            tk.Button(self.frame, text="Excluir",
                      command=lambda: excluir('canal', self, app_principal),
                      bg="red").grid(row=2, column=0, padx=5, pady=5, sticky="e")

            tk.Button(frame_edicoes,
                      text="Atualizar",
                      command=lambda: editar('canal', self, app_principal),
                      bg="green").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=5)
        else:
            if self.canal_form:
                self.canal_form.title("Novo Canal")
            frame_edicoes.config(text='Novo Canal')
            tk.Button(frame_edicoes,
                      text="Adicionar",
                      command=lambda: adicionar('canal', self, app_principal),
                      bg="cyan").grid(row=1, column=2, padx=5, pady=5, sticky="ew", rowspan=5)

    def main(self, root, app_principal):
        '''
        Inicializa e exibe o formulário de gerenciamento de canais.
        '''
        self.frame = configurar_main_frame(self.canal_form)
        self.criar_frame_busca(app_principal)
        frame_edicoes = self.criar_frame_edicoes(app_principal)
        self.criar_lista_canais(app_principal)
        self.configurar_botoes(frame_edicoes, app_principal)

def main(root):
    '''
    Função principal para inicializar o formulário de canais.
    '''
    # Importar app para acessar a instância principal
    from src.app import app
    form = FormCanal(root, app_principal=app)
    form.main(root, app)

if __name__ == "__main__":
    main(None)
