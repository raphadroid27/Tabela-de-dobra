"""
Módulo utilitário para gerenciamento de usuários no aplicativo de cálculo de dobras.
"""
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


def novo_usuario():
    """
    Cria um novo usuário com o nome e senha fornecidos.
    """
    # Verificar se os widgets foram inicializados
    if g.USUARIO_ENTRY is None or g.SENHA_ENTRY is None:
        messagebox.showerror("Erro", "Interface não inicializada corretamente.")
        return

    novo_usuario_nome = g.USUARIO_ENTRY.get() if g.USUARIO_ENTRY else ""
    novo_usuario_senha = g.SENHA_ENTRY.get() if g.SENHA_ENTRY else ""
    senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()

    if novo_usuario_nome == "" or novo_usuario_senha == "":
        messagebox.showerror("Erro", "Preencha todos os campos.",
                             parent=g.AUTEN_FORM)
        return

    # Verificar se o usuário já existe
    usuario_obj = session.query(Usuario).filter_by(nome=novo_usuario_nome).first()
    if usuario_obj:
        messagebox.showerror("Erro", "Usuário já existente.",
                             parent=g.AUTEN_FORM if g.AUTEN_FORM else None)
        return

    # Criar o novo usuário
    if g.ADMIN_VAR is None:
        messagebox.showerror("Erro", "Variável de administrador não inicializada.")
        return

    admin_value = g.ADMIN_VAR.get() if g.ADMIN_VAR else "viewer"
    usuario = Usuario(nome=novo_usuario_nome, senha=senha_hash, role=admin_value)
    session.add(usuario)

    # Usar tratativa_erro para tratar erros e confirmar a operação
    tratativa_erro()  # Chamar a função para tratar erros antes de continuar
    messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso.",
                        parent=g.AUTEN_FORM if g.AUTEN_FORM else None)

    if g.AUTEN_FORM is not None:
        g.AUTEN_FORM.destroy()

    habilitar_janelas()


def login():
    """
    Realiza o login do usuário com o nome e senha fornecidos.
    Se o usuário não existir, cria um novo usuário.
    """
    # Verificar se os widgets foram inicializados
    if g.USUARIO_ENTRY is None or g.SENHA_ENTRY is None:
        messagebox.showerror("Erro", "Interface não inicializada corretamente.")
        return

    g.USUARIO_NOME = g.USUARIO_ENTRY.get() if g.USUARIO_ENTRY else ""
    usuario_senha = g.SENHA_ENTRY.get() if g.SENHA_ENTRY else ""

    usuario_obj = session.query(Usuario).filter_by(nome=g.USUARIO_NOME).first()

    if usuario_obj:
        # Usar getattr para acessar o valor da coluna de forma segura
        senha_db = getattr(usuario_obj, 'senha', None)
        if senha_db == "nova_senha":
            nova_senha = simpledialog.askstring(
                "Nova Senha",
                "Digite uma nova senha:",
                show="*",
                parent=g.AUTEN_FORM if g.AUTEN_FORM else None)
            if nova_senha:
                # Usar setattr para atribuir valor à coluna de forma segura
                senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                setattr(usuario_obj, 'senha', senha_hash)
                tratativa_erro()
                messagebox.showinfo(
                    "Sucesso",
                    "Senha alterada com sucesso. Faça login novamente.",
                    parent=g.AUTEN_FORM if g.AUTEN_FORM else None)
                return
        elif senha_db == hashlib.sha256(usuario_senha.encode()).hexdigest():
            messagebox.showinfo("Login", "Login efetuado com sucesso.",
                                parent=g.AUTEN_FORM if g.AUTEN_FORM else None)
            g.USUARIO_ID = usuario_obj.id
            if g.AUTEN_FORM is not None:
                g.AUTEN_FORM.destroy()
            if g.PRINC_FORM is not None:
                titulo = f"Cálculo de Dobra - {getattr(usuario_obj, 'nome', 'Usuário')}"
                g.PRINC_FORM.title(titulo)
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos.",
                                 parent=g.AUTEN_FORM if g.AUTEN_FORM else None)
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.",
                             parent=g.AUTEN_FORM if g.AUTEN_FORM else None)

    habilitar_janelas()


def logado(tipo):
    """
    Verifica se o usuário está logado antes de permitir ações em formulários específicos.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if g.USUARIO_ID is None:
        messagebox.showerror("Erro", "Login requerido.", parent=config['form'])
        return False
    return True


def tem_permissao(tipo, role_requerida):
    """
    Verifica se o usuário tem permissão para realizar uma ação específica.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    usuario_obj = session.query(Usuario).filter_by(id=g.USUARIO_ID).first()
    if not usuario_obj:
        messagebox.showerror("Erro", "Você não tem permissão para acessar esta função.",
                             parent=config['form'])
        return False

    # Permitir hierarquia de permissões
    roles_hierarquia = ["viewer", "editor", "admin"]
    usuario_role = getattr(usuario_obj, 'role', 'viewer')
    required_index = roles_hierarquia.index(role_requerida)
    user_index = roles_hierarquia.index(usuario_role)
    if user_index < required_index:
        messagebox.showerror("Erro", f"Permissão '{role_requerida}' requerida.")
        return False
    return True


def logout():
    """
    Realiza o logout do usuário atual.
    """
    if g.USUARIO_ID is None:
        messagebox.showerror("Erro", "Nenhum usuário logado.")
        return

    g.USUARIO_ID = None
    if g.PRINC_FORM is not None:
        g.PRINC_FORM.title("Cálculo de Dobra")
    messagebox.showinfo("Logout", "Logout efetuado com sucesso.")


def resetar_senha():
    """
    Reseta a senha do usuário selecionado na lista de usuários.
    """
    if g.LIST_USUARIO is None:
        messagebox.showerror("Erro", "Lista de usuários não inicializada.")
        return

    selected_item = g.LIST_USUARIO.selection() if g.LIST_USUARIO else []
    if not selected_item:
        messagebox.showwarning("Aviso",
                               "Selecione um usuário para resetar a senha.",
                               parent=g.USUAR_FORM if g.USUAR_FORM else None)
        return

    if g.LIST_USUARIO is None:
        messagebox.showerror("Erro", "Lista de usuários não disponível.")
        return

    user_id = g.LIST_USUARIO.item(selected_item, "values")[0] if g.LIST_USUARIO else None
    if user_id is None:
        messagebox.showerror("Erro", "Erro ao obter ID do usuário.",
                             parent=g.USUAR_FORM if g.USUAR_FORM else None)
        return

    novo_password = "nova_senha"  # Defina a nova senha padrão aqui
    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()
    if usuario_obj:
        setattr(usuario_obj, 'senha', novo_password)
        tratativa_erro()
        messagebox.showinfo("Sucesso", "Senha resetada com sucesso.",
                            parent=g.USUAR_FORM if g.USUAR_FORM else None)
    else:
        messagebox.showerror("Erro", "Usuário não encontrado.",
                             parent=g.USUAR_FORM if g.USUAR_FORM else None)


def excluir_usuario():
    """
    Exclui o usuário selecionado na lista de usuários.
    """
    # Validações iniciais
    if not tem_permissao('usuario', 'admin') or g.LIST_USUARIO is None:
        return

    selected_items = g.LIST_USUARIO.selection() if g.LIST_USUARIO else []
    if not selected_items:
        messagebox.showwarning("Aviso", "Selecione um usuário para excluir.",
                               parent=g.USUAR_FORM if g.USUAR_FORM else None)
        return

    # Obter dados do usuário selecionado
    selected_item = selected_items[0]
    item = g.LIST_USUARIO.item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(Usuario).filter_by(id=obj_id).first()

    erro_msg = None
    if obj is None:
        erro_msg = "Usuário não encontrado."
    elif getattr(obj, 'role', None) == "admin":
        erro_msg = "Não é possível excluir um administrador."

    if erro_msg:
        messagebox.showerror("Erro", erro_msg,
                             parent=g.USUAR_FORM if g.USUAR_FORM else None)
        return

    # Confirmar exclusão
    aviso = messagebox.askyesno("Atenção!",
                                "Tem certeza que deseja excluir o usuário?",
                                parent=g.USUAR_FORM if g.USUAR_FORM else None)
    if aviso:
        session.delete(obj)
        tratativa_erro()
        if g.LIST_USUARIO is not None:
            g.LIST_USUARIO.delete(selected_item)
        messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!",
                            parent=g.USUAR_FORM if g.USUAR_FORM else None)
        listar('usuario')


def tornar_editor():
    """
    Promove o usuário selecionado a editor.
    """
    if g.LIST_USUARIO is None:
        messagebox.showerror("Erro", "Lista de usuários não disponível.")
        return

    selected_item = g.LIST_USUARIO.selection() if g.LIST_USUARIO else []
    if not selected_item:
        messagebox.showwarning("Aviso",
                               "Selecione um usuário para promover a editor.",
                               parent=g.USUAR_FORM if g.USUAR_FORM else None)
        return

    if g.LIST_USUARIO is None:
        messagebox.showerror("Erro", "Lista de usuários não disponível.")
        return

    user_id = g.LIST_USUARIO.item(selected_item, "values")[0] if g.LIST_USUARIO else None
    if user_id is None:
        messagebox.showerror("Erro", "Erro ao obter ID do usuário.",
                             parent=g.USUAR_FORM if g.USUAR_FORM else None)
        return

    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()

    if usuario_obj:
        # Usar getattr para acessar o valor da coluna de forma segura
        usuario_role = getattr(usuario_obj, 'role', None)
        if usuario_role == "admin":
            messagebox.showerror("Erro",
                                 "O usuário já é um administrador.",
                                 parent=g.USUAR_FORM if g.USUAR_FORM else None)
            return
        if usuario_role == "editor":
            messagebox.showinfo("Informação",
                                "O usuário já é um editor.",
                                parent=g.USUAR_FORM if g.USUAR_FORM else None)
            return

        # Usar setattr para atribuir valor à coluna de forma segura
        setattr(usuario_obj, 'role', "editor")
        tratativa_erro()
        messagebox.showinfo("Sucesso",
                            "Usuário promovido a editor com sucesso.",
                            parent=g.USUAR_FORM if g.USUAR_FORM else None)
        listar('usuario')  # Atualiza a lista de usuários na interface
    else:
        messagebox.showerror("Erro",
                             "Usuário não encontrado.",
                             parent=g.USUAR_FORM if g.USUAR_FORM else None)
