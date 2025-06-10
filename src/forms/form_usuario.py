'''
# Formulário de Gerenciamento de Usuários
# Este módulo implementa uma interface gráfica para gerenciar usuários do sistema.
# As funcionalidades incluem redefinir senhas, alterar permissões e excluir usuários.
# A interface é construída com a biblioteca tkinter, utilizando o módulo globals
# para variáveis globais e o módulo funcoes para operações relacionadas ao banco de dados.
'''
import tkinter as tk
from tkinter import ttk, messagebox
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.interface import (listar, limpar_busca, configurar_main_frame)
from src.utils.utilitarios import obter_caminho_icone
from src.utils.operacoes_crud import buscar
from src.utils.usuarios import (tornar_editor,
                                 resetar_senha,
                                 excluir_usuario
                                 )
from src.utils.banco_dados import session
from src.models.models import Usuario
from src.config import globals as g

class FormUsuario:

    def __init__(self, root, app_principal):
        '''
        Configura a janela principal do formulário de usuários.
        '''
        # Criar o formulário (permissão já foi verificada na função main)
        self.usuario_form = tk.Toplevel(root)
        self.usuario_form.title("Editar/Excluir Usuário")
        self.usuario_form.geometry("300x280")
        self.usuario_form.resizable(False, False)
        
        icone_path = obter_caminho_icone()
        self.usuario_form.iconbitmap(icone_path)

        no_topo(self.usuario_form, app_principal)
        posicionar_janela(self.usuario_form, app_principal, 'centro')

    def criar_frame_busca(self, app_principal):
        '''
        Cria o frame de busca.
        '''
        frame_busca = tk.LabelFrame(self.frame, text='Filtrar Usuários', pady=5)
        frame_busca.grid(row=0, column=0, padx=5, pady=5, sticky="ew", columnspan=3)

        for i in range(3):
            frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

        tk.Label(frame_busca, text="Usuário:").grid(row=0, column=0)
        self.usuario_busca_entry = tk.Entry(frame_busca)
        self.usuario_busca_entry.grid(row=0, column=1, sticky="ew")
        self.usuario_busca_entry.bind("<KeyRelease>", lambda event: buscar('usuario', app_principal, self))

        tk.Button(frame_busca,
                  text="Limpar",
                  command=lambda: limpar_busca('usuario', self)).grid(row=0, column=2, padx=5, pady=5)

    def criar_lista_usuarios(self, app_principal):
        '''
        Cria a lista de usuários.
        '''
        columns = ("Id", "Nome", "Permissões")
        self.usuario_lista = ttk.Treeview(self.frame, columns=columns, show="headings")
        self.usuario_lista["displaycolumns"] = ("Nome", "Permissões")
        
        for col in columns:
            self.usuario_lista.heading(col, text=col)
            self.usuario_lista.column(col, anchor="center", width=20)

        self.usuario_lista.grid(row=1, column=0, padx=5, pady=5, sticky="ew", columnspan=3)
        listar('usuario', ui=self)

    def configurar_botoes(self, app_principal):
        '''
        Configura os botões de ação (Tornar Editor, Resetar Senha, Excluir).
        '''
        tk.Button(self.frame,
                 text="Tornar Editor",
                 command=lambda: tornar_editor(self),
                 bg="green",
                 width=10).grid(row=2, column=0, padx=5, pady=5, sticky="w")

        tk.Button(self.frame,
                  text="Resetar Senha",
                  command=lambda: resetar_senha(self),
                  bg="yellow",
                  width=10).grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        tk.Button(self.frame,
                  text="Excluir",
                  command=lambda: excluir_usuario(self),
                  bg="red",
                  width=10).grid(row=2, column=2, padx=5, pady=5, sticky="e")

    def main(self, root, app_principal):
        '''
        Inicializa e exibe o formulário de gerenciamento de usuários.
        '''
        self.frame = configurar_main_frame(self.usuario_form)
        
        for i in range(3):
            self.frame.columnconfigure(i, weight=1)

        for i in range(3):
            self.frame.rowconfigure(i, weight=1 if i == 1 else 0)

        self.criar_frame_busca(app_principal)
        self.criar_lista_usuarios(app_principal)
        self.configurar_botoes(app_principal)

def main(root, app_principal=None):
    '''
    Função principal para inicializar o formulário de usuários.
    '''
    # Verificar permissão diretamente sem usar obter_configuracoes
    
    try:
        # Verificar se há usuário logado
        if not g.USUARIO_ID:
            messagebox.showerror("Erro", "Você precisa estar logado para acessar esta função.")
            return
        
        # Buscar o usuário no banco de dados
        usuario_obj = session.query(Usuario).filter_by(id=g.USUARIO_ID).first()
        if not usuario_obj or usuario_obj.role != "admin":
            messagebox.showerror("Erro", "Você não tem permissão para acessar esta função.")
            return
    
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar permissões: {str(e)}")
        return
    
    # Se tem permissão, criar o formulário
    form = FormUsuario(root)
    form.main(root, app_principal)

if __name__ == "__main__":
    main(None)
