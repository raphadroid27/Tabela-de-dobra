'''
Módulo utilitário para gerenciamento de usuários no aplicativo de cálculo de dobras.
'''
import tkinter as tk
from tkinter import messagebox, simpledialog
import hashlib
from src.config import globals as g
from src.models.models import Usuario
from src.utils.banco_dados import (session,
                                   tratativa_erro,
                                   obter_configuracoes
                                   )
from src.utils.janelas import habilitar_janelas
from src.utils.operacoes_crud import listar

def novo_usuario():
    '''
    Cria um novo usuário com o nome e senha fornecidos.
    '''
    novo_usuario_nome = g.USUARIO_ENTRY.get()
    novo_usuario_senha = g.SENHA_ENTRY.get()
    senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()

    if novo_usuario_nome == "" or novo_usuario_senha == "":
        messagebox.showerror("Erro", "Preencha todos os campos.", parent=g.AUTEN_FORM)
        return

    # Verificar se o usuário já existe
    usuario_obj = session.query(Usuario).filter_by(nome=novo_usuario_nome).first()
    if usuario_obj:
        messagebox.showerror("Erro", "Usuário já existente.", parent=g.AUTEN_FORM)
        return

    # Criar o novo usuário
    usuario = Usuario(nome=novo_usuario_nome, senha=senha_hash, role=g.ADMIN_VAR.get())
    session.add(usuario)

    # Usar tratativa_erro para tratar erros e confirmar a operação
    tratativa_erro()  # Chamar a função para tratar erros antes de continuar
    messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso.", parent=g.AUTEN_FORM)
    g.AUTEN_FORM.destroy()

    habilitar_janelas()

def login():
    '''
    Realiza o login do usuário com o nome e senha fornecidos.
    Se o usuário não existir, cria um novo usuário.
    '''
    g.USUARIO_NOME = g.USUARIO_ENTRY.get()
    usuario_senha = g.SENHA_ENTRY.get()

    usuario_obj = session.query(Usuario).filter_by(nome=g.USUARIO_NOME).first()

    if usuario_obj:
        if usuario_obj.senha == "nova_senha":
            nova_senha = simpledialog.askstring("Nova Senha",
                                                "Digite uma nova senha:",
                                                show="*",
                                                parent=g.AUTEN_FORM)
            if nova_senha:
                usuario_obj.senha = hashlib.sha256(nova_senha.encode()).hexdigest()
                tratativa_erro()
                messagebox.showinfo("Sucesso",
                                    "Senha alterada com sucesso. Faça login novamente.",
                                    parent=g.AUTEN_FORM)
                return
        elif usuario_obj.senha == hashlib.sha256(usuario_senha.encode()).hexdigest():
            messagebox.showinfo("Login", "Login efetuado com sucesso.", parent=g.AUTEN_FORM)
            g.USUARIO_ID = usuario_obj.id
            g.AUTEN_FORM.destroy()
            g.PRINC_FORM.title(f"Cálculo de Dobra - {usuario_obj.nome}")
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos.", parent=g.AUTEN_FORM)
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.", parent=g.AUTEN_FORM)

    habilitar_janelas()

def logado(tipo):
    '''
    Verifica se o usuário está logado antes de permitir ações em formulários específicos.
    '''
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if g.USUARIO_ID is None:
        messagebox.showerror("Erro", "Login requerido.", parent=config['form'])
        return False
    return True

def tem_permissao(tipo, role_requerida):
    '''
    Verifica se o usuário tem permissão para realizar uma ação específica.
    '''
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    usuario_obj = session.query(Usuario).filter_by(id=g.USUARIO_ID).first()
    if not usuario_obj:
        messagebox.showerror("Erro", "Você não tem permissão para acessar esta função.",
                             parent=config['form'])
        return False
    # Permitir hierarquia de permissões
    roles_hierarquia = ["viewer", "editor", "admin"]
    if roles_hierarquia.index(usuario_obj.role) < roles_hierarquia.index(role_requerida):
        messagebox.showerror("Erro", f"Permissão '{role_requerida}' requerida.")
        return False
    return True

def logout():
    '''
    Realiza o logout do usuário atual.
    '''
    if g.USUARIO_ID is None:
        messagebox.showerror("Erro", "Nenhum usuário logado.")
        return
    g.USUARIO_ID = None
    g.PRINC_FORM.title("Cálculo de Dobra")
    messagebox.showinfo("Logout", "Logout efetuado com sucesso.")

def resetar_senha():
    '''
    Reseta a senha do usuário selecionado na lista de usuários.
    '''
    selected_item = g.LIST_USUARIO.selection()
    if not selected_item:
        tk.messagebox.showwarning("Aviso",
                                  "Selecione um usuário para resetar a senha.",
                                  parent=g.USUAR_FORM)
        return

    user_id = g.LIST_USUARIO.item(selected_item, "values")[0]
    novo_password = "nova_senha"  # Defina a nova senha padrão aqui
    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()
    if usuario_obj:
        usuario_obj.senha = novo_password
        tratativa_erro()
        tk.messagebox.showinfo("Sucesso", "Senha resetada com sucesso.", parent=g.USUAR_FORM)
    else:
        tk.messagebox.showerror("Erro", "Usuário não encontrado.", parent=g.USUAR_FORM)

def excluir_usuario():
    '''
    Exclui o usuário selecionado na lista de usuários.
    '''
    if not tem_permissao('usuario', 'admin'):
        return

    if g.LIST_USUARIO is None:
        return

    selected_item = g.LIST_USUARIO.selection()[0]
    item = g.LIST_USUARIO.item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(Usuario).filter_by(id=obj_id).first()
    if obj is None:
        messagebox.showerror("Erro", "Usuário não encontrado.", parent=g.USUAR_FORM)
        return

    if obj.role == "admin":
        messagebox.showerror("Erro",
                             "Não é possível excluir um administrador.",
                             parent=g.USUAR_FORM)
        return

    aviso = messagebox.askyesno("Atenção!",
                                "Tem certeza que deseja excluir o usuário?",
                                parent=g.USUAR_FORM)
    if not aviso:
        return

    session.delete(obj)
    tratativa_erro()
    g.LIST_USUARIO.delete(selected_item)
    messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!", parent=g.USUAR_FORM)

    listar('usuario')

def tornar_editor():
    '''
    Promove o usuário selecionado a editor.
    '''
    selected_item = g.LIST_USUARIO.selection()
    if not selected_item:
        tk.messagebox.showwarning("Aviso",
                                  "Selecione um usuário para promover a editor.",
                                  parent=g.USUAR_FORM)
        return

    user_id = g.LIST_USUARIO.item(selected_item, "values")[0]
    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()

    if usuario_obj:
        if usuario_obj.role == "admin":
            tk.messagebox.showerror("Erro",
                                    "O usuário já é um administrador.",
                                    parent=g.USUAR_FORM)
            return
        if usuario_obj.role == "editor":
            tk.messagebox.showinfo("Informação",
                                   "O usuário já é um editor.",
                                   parent=g.USUAR_FORM)
            return

        usuario_obj.role = "editor"
        tratativa_erro()
        tk.messagebox.showinfo("Sucesso",
                               "Usuário promovido a editor com sucesso.",
                               parent=g.USUAR_FORM)
        listar('usuario')  # Atualiza a lista de usuários na interface
    else:
        tk.messagebox.showerror("Erro",
                                "Usuário não encontrado.",
                                parent=g.USUAR_FORM)
