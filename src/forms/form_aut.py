'''
# Formulário de Autenticação
# Este módulo implementa uma interface gráfica para autenticação de usuários no sistema.
# As funcionalidades incluem login de usuários existentes e criação de novos usuários,
# com a possibilidade de definir permissões administrativas. A interface é construída
# com a biblioteca tkinter, utilizando o módulo globals para variáveis globais e o
# módulo funcoes para operações auxiliares. O banco de dados é gerenciado com SQLAlchemy.
'''
import tkinter as tk
from src.utils.banco_dados import session
from src.models import Usuario
from src.utils.usuarios import login, novo_usuario
from src.utils.janelas import (desabilitar_janelas,
                              habilitar_janelas,
                              posicionar_janela
                              )
from src.utils.utilitarios import obter_caminho_icone

class FormAutenticacao:

    def __init__(self, root, app_principal=None, login=True):
        '''
        Configura a janela principal do formulário de autenticação.
        '''
        self.app_principal = app_principal
        self.login = login  # Adicionar o atributo login
        
        # Criar a janela de autenticação
        self.auten_form = tk.Toplevel(root)
        
        self.auten_form.geometry("200x120")
        self.auten_form.resizable(False, False)
        
        try:
            icone_path = obter_caminho_icone()
            self.auten_form.iconbitmap(icone_path)
        except:
            pass  # Se não encontrar o ícone, continua sem ele
        
        self.auten_form.attributes('-toolwindow', True)
        self.auten_form.attributes("-topmost", True)
        self.auten_form.focus()
        
        desabilitar_janelas(app_principal, excluir_janela=self.auten_form)
        self.auten_form.protocol("WM_DELETE_WINDOW", lambda: [habilitar_janelas(app_principal),
                                                             self.auten_form.destroy()
                                                             if self.auten_form
                                                             else None])

    def criar_frame_principal(self):
        '''
        Cria o frame principal do formulário.
        '''
        self.main_frame = tk.Frame(self.auten_form)
        self.main_frame.pack(pady=5, padx=5, fill='both', expand=True)

        for i in range(2):
            self.main_frame.columnconfigure(i, weight=1)
        for i in range(4):
            self.main_frame.rowconfigure(i, weight=1)

    def criar_campos_usuario_senha(self):
        '''
        Cria os campos de usuário e senha.
        '''
        tk.Label(self.main_frame, text="Usuário:").grid(row=0, column=0, padx=5, pady=5)
        self.usuario_entry = tk.Entry(self.main_frame)
        self.usuario_entry.focus()
        self.usuario_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.main_frame, text="Senha:").grid(row=1, column=0, padx=5, pady=5)
        self.senha_entry = tk.Entry(self.main_frame, show="*")
        self.senha_entry.grid(row=1, column=1, padx=5, pady=5)

    def verificar_admin_existente(self):
        '''
        Verifica se já existe um administrador no sistema.
        '''
        return session.query(Usuario).filter(Usuario.role == 'admin').first()

    def configurar_campo_admin(self, admin_existente):
        '''
        Configura o campo de administrador para novos usuários.
        '''
        self.admin_var = tk.StringVar()
        
        if not admin_existente:
            self.auten_form.geometry("200x150")
            tk.Label(self.main_frame, text="Admin:").grid(row=2, column=0, padx=5, pady=5)
            self.admin_var.set('viewer')  # Valor padrão quando desmarcado
            admin_checkbox = tk.Checkbutton(self.main_frame,
                           variable=self.admin_var,
                                          onvalue='admin',
                                          offvalue='viewer')
            admin_checkbox.grid(row=2, column=1, padx=5, pady=5)
        else:
            # Se já existe admin, o novo usuário não pode ser admin
            self.admin_var.set('viewer')

    def configurar_botoes(self):
        '''
        Configura os botões de ação (Login ou Salvar).
        '''
        admin_existente = self.verificar_admin_existente()

        if self.login:
            self.auten_form.title("Login")
            tk.Button(self.main_frame,
                     text="Login",
                     command=lambda: login(self.app_principal, self)).grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        else:
            self.configurar_campo_admin(admin_existente)
            self.auten_form.title("Novo Usuário")
            tk.Button(self.main_frame,
                     text="Salvar",
                     command=lambda: novo_usuario(self)).grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def main(self, root, app_principal=None):
        '''
        Inicializa e exibe o formulário de autenticação.
        '''
        #posicionar_janela(self.auten_form, 'centro')
        self.criar_frame_principal()
        self.criar_campos_usuario_senha()
        self.configurar_botoes()

def main(root, app_principal=None, login=True):
    '''
    Função principal para inicializar o formulário de autenticação.
    '''
    form = FormAutenticacao(root, app_principal=app_principal, login=login)
    form.main(root, app_principal)
