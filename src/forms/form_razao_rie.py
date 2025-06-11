'''
Módulo para exibir o formulário de cálculo de razão raio interno / espessura.
'''
import tkinter as tk
from tkinter import ttk
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.utilitarios import obter_caminho_icone
from src.utils.calculos import razao_ri_espessura
from src.config import globals as g

class FormRaioInternoEspessura:
    '''Classe para o formulário de cálculo de razão raio interno / espessura.
    Esta classe inicializa a interface gráfica e exibe os valores calculados
    e os fatores K correspondentes.    A classe utiliza a biblioteca tkinter para a construção da interface e
    o módulo globals para armazenar variáveis globais.
    '''
    rie_form = None
    instancia_ativa = None  # Variável de classe para armazenar a instância ativa
    
    def __init__(self, root, app_principal=None, cabecalho_ui=None, rie_ui=None):
        '''
        Inicializa e exibe o formulário de cálculo de razão raio interno / espessura.
        Configura a interface gráfica para exibir os valores e fatores K correspondentes.
        '''
        if self.rie_form:
            self.rie_form.destroy()

        # Definir esta instância como a ativa
        FormRaioInternoEspessura.instancia_ativa = self

        self.rie_form = tk.Toplevel(root)
        self.rie_form.title("Raio Interno / Espessura")
        self.rie_form.geometry("240x280")
        self.rie_form.resizable(False, False)
        
        # Configurar protocolo de fechamento para limpar a instância ativa
        self.rie_form.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Define o ícone
        icone_path = obter_caminho_icone()
        self.rie_form.iconbitmap(icone_path)

        no_topo(self.rie_form, app_principal)
        posicionar_janela(self.rie_form, app_principal, None)

        main_frame = tk.Frame(self.rie_form)
        main_frame.pack(pady=5, padx=5, fill='both', expand=True)

        main_frame.grid_rowconfigure(0, weight=0)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)

        tk.Label(main_frame, text='Razão Raio Interno / Espessura: ').grid(row=0, column=0, sticky='w')
        self.razao_rie_widget = tk.Label(main_frame, text="", relief="sunken", width=20)
        self.razao_rie_widget.grid(row=0, column=1, sticky='e', padx=5, pady=5)

        def create_table(main_frame, data):
            # Frame para a tabela e barra de rolagem
            table_frame = tk.Frame(main_frame)
            table_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

            # Configuração da barra de rolagem vertical
            scrollbar = tk.Scrollbar(table_frame, orient='vertical')
            scrollbar.pack(side='right', fill='y')

            # Configuração da tabela
            tree = ttk.Treeview(table_frame,
                                columns=('Raio/Esp', 'Fator K'),
                                show='headings',
                                yscrollcommand=scrollbar.set
                                )
            tree.heading('Raio/Esp', text='Raio/Esp')
            tree.heading('Fator K', text='Fator K')
            tree.column('Raio/Esp', width=100, anchor='center')
            tree.column('Fator K', width=100, anchor='center')

            # Vincula a barra de rolagem à tabela
            scrollbar.config(command=tree.yview)

            # Inserção dos dados na tabela
            for raio, fator_k in data.items():
                tree.insert('', 'end', values=(raio, fator_k))

            tree.pack(fill='both', expand=True)

        avisolabel = tk.Message(
            main_frame,
            text='Atenção: Os valores apresentados na tabela são teóricos. '
                'Utilize-os apenas na ausência de dados mais precisos.',
            width=220,
            justify='left',
            fg='red',
            font=('Arial', 10, 'bold')
        )
        avisolabel.grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=5)

        razao_ri_espessura(cabecalho_ui, self)
        create_table(main_frame, g.RAIO_K)

    def _on_closing(self):
        '''
        Método chamado quando a janela é fechada.
        Limpa a referência da instância ativa.
        '''
        FormRaioInternoEspessura.instancia_ativa = None
        self.rie_form.destroy()

def main(root, app_principal=None):
    '''
    Função principal para inicializar o formulário de cálculo de razão raio interno / espessura.
    '''
    form = FormRaioInternoEspessura(root, app_principal=app_principal, 
                                    cabecalho_ui=app_principal.cabecalho_ui if app_principal else None, 
                                    rie_ui=None)

if __name__ == "__main__":
    main(None)
