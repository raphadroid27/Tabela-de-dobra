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
from src.utils.interface import listar

def novo_usuario(auten_ui):
    '''
    Cria um novo usuário com o nome e senha fornecidos.
    '''
    novo_usuario_nome = auten_ui.usuario_entry.get()
    novo_usuario_senha = auten_ui.senha_entry.get()
    senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()

    if novo_usuario_nome == "" or novo_usuario_senha == "":
        messagebox.showerror("Erro", "Preencha todos os campos.", parent=auten_ui.auten_form)
        return

    # Verificar se o usuário já existe
    usuario_obj = session.query(Usuario).filter_by(nome=novo_usuario_nome).first()
    if usuario_obj:
        messagebox.showerror("Erro", "Usuário já existente.", parent=auten_ui.auten_form)
        return

    # Criar o novo usuário
    usuario = Usuario(nome=novo_usuario_nome, senha=senha_hash, role=auten_ui.admin_var.get())
    session.add(usuario)

    # Usar tratativa_erro para tratar erros e confirmar a operação
    tratativa_erro()  # Chamar a função para tratar erros antes de continuar
    messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso.", parent=auten_ui.auten_form)
    auten_ui.auten_form.destroy()

    habilitar_janelas(auten_ui.app_principal)

def login(app_principal, auten_ui):
    '''
    Realiza o login do usuário com o nome e senha fornecidos.
    Se o usuário não existir, cria um novo usuário.
    '''
    usuario_nome = auten_ui.usuario_entry.get()
    usuario_senha = auten_ui.senha_entry.get()

    usuario_obj = session.query(Usuario).filter_by(nome=usuario_nome).first()

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
            messagebox.showinfo("Login", "Login efetuado com sucesso.", parent=auten_ui.auten_form)
            g.USUARIO_ID = usuario_obj.id
            auten_ui.auten_form.destroy()
            app_principal.janela_principal.title(f"Cálculo de Dobra - {usuario_obj.nome}")
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos.", parent=auten_ui.auten_form)
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.", parent=auten_ui.auten_form)

    habilitar_janelas(app_principal)

def tem_permissao(tipo, role_requerida, form_ui):
    '''
    Verifica se o usuário tem permissão para realizar uma ação específica.
    '''
    configuracoes = obter_configuracoes(form_ui)
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

def logout(app_principal):
    '''
    Realiza o logout do usuário atual.
    '''
    if g.USUARIO_ID is None:
        messagebox.showerror("Erro", "Nenhum usuário logado.")
        return
    g.USUARIO_ID = None
    app_principal.janela_principal.title("Cálculo de Dobra")
    messagebox.showinfo("Logout", "Logout efetuado com sucesso.")

def resetar_senha(form_ui):
    '''
    Reseta a senha do usuário selecionado na lista de usuários.
    '''
    selected_item = form_ui.usuario_lista.selection()
    if not selected_item:
        tk.messagebox.showwarning("Aviso",
                                  "Selecione um usuário para resetar a senha.",
                                  parent=form_ui.usuario_form)
        return

    user_id = form_ui.usuario_lista.item(selected_item, "values")[0]
    novo_password = "nova_senha"  # Defina a nova senha padrão aqui
    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()
    if usuario_obj:
        usuario_obj.senha = novo_password
        tratativa_erro()
        tk.messagebox.showinfo("Sucesso", "Senha resetada com sucesso.", parent=form_ui.usuario_form)
    else:
        tk.messagebox.showerror("Erro", "Usuário não encontrado.", parent=form_ui.usuario_form)

def excluir_usuario(form_ui):
    '''
    Exclui o usuário selecionado na lista de usuários.
    '''
    if not tem_permissao('usuario', 'admin', form_ui):
        return

    if form_ui.usuario_lista is None:
        return

    selected_item = form_ui.usuario_lista.selection()[0]
    item = form_ui.usuario_lista.item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(Usuario).filter_by(id=obj_id).first()
    if obj is None:
        messagebox.showerror("Erro", "Usuário não encontrado.", parent=form_ui.usuario_form)
        return

    if obj.role == "admin":
        messagebox.showerror("Erro",
                             "Não é possível excluir um administrador.",
                             parent=form_ui.usuario_form)
        return

    aviso = messagebox.askyesno("Atenção!",
                                "Tem certeza que deseja excluir o usuário?",
                                parent=form_ui.usuario_form)
    if not aviso:
        return

    session.delete(obj)
    tratativa_erro()
    form_ui.usuario_lista.delete(selected_item)
    messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!", parent=g.USUAR_FORM)

    listar('usuario', form_ui)

def tornar_editor(form_ui):
    '''
    Promove o usuário selecionado a editor.
    '''
    selected_item = form_ui.usuario_lista.selection()
    if not selected_item:
        tk.messagebox.showwarning("Aviso",
                                  "Selecione um usuário para promover a editor.",
                                  parent=form_ui.usuario_form)
        return

    user_id = form_ui.usuario_lista.item(selected_item, "values")[0]
    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()

    if usuario_obj:
        if usuario_obj.role == "admin":
            tk.messagebox.showerror("Erro",
                                    "O usuário já é um administrador.",
                                    parent=form_ui.usuario_form)
            return
        if usuario_obj.role == "editor":
            tk.messagebox.showinfo("Informação",
                                   "O usuário já é um editor.",
                                   parent=form_ui.usuario_form)
            return

        usuario_obj.role = "editor"
        tratativa_erro()
        tk.messagebox.showinfo("Sucesso",
                               "Usuário promovido a editor com sucesso.",
                               parent=form_ui.usuario_form)
        listar('usuario', form_ui)
    else:
        tk.messagebox.showerror("Erro",
                                "Usuário não encontrado.",
                                parent=form_ui.usuario_form)
