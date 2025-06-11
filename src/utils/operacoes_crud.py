'''
Este módulo contém funções auxiliares para manipulação de dados no aplicativo de cálculo de dobras.
Inclui operações CRUD (Criar, Ler, Atualizar, Excluir) para os tipos de dados: dedução, espessura, 
material e canal.
'''
import tkinter as tk
from tkinter import messagebox
import re
from src.utils.banco_dados import (session,
                         salvar_no_banco,
                         tratativa_erro,
                         registrar_log,
                         obter_configuracoes
                         )
from src.utils.usuarios import tem_permissao
from src.config import globals as g
from src.models.models import Espessura, Material, Canal, Deducao
from src.utils.interface import atualizar_widgets, listar

def adicionar(tipo, form_ui, app_principal):
    '''
    Adiciona um novo item ao banco de dados com base no tipo especificado.
    '''
    if not tem_permissao(tipo, 'editor', form_ui):
        return

    if tipo == 'dedução':
        adicionar_deducao(form_ui)
    elif tipo == 'espessura':
        adicionar_espessura(form_ui)
    elif tipo == 'material':
        adicionar_material(form_ui)
    elif tipo == 'canal':
        adicionar_canal(form_ui)

    limpar_campos(tipo, form_ui)
    listar(tipo, form_ui)
    atualizar_widgets(app_principal.cabecalho_ui, form_ui, tipo)
    buscar(tipo, form_ui)

def adicionar_deducao(form_ui):
    '''
    Lógica para adicionar uma nova dedução.
    '''
    espessura_valor = form_ui.deducao_espessura_combo.get()
    canal_valor = form_ui.deducao_canal_combo.get()
    material_nome = form_ui.deducao_material_combo.get()
    nova_observacao_valor = form_ui.deducao_observacao_entry.get()
    nova_forca_valor = form_ui.deducao_forca_entry.get()

    if not all([espessura_valor, canal_valor, material_nome, form_ui.deducao_valor_entry.get()]):
        messagebox.showerror("Erro",
                             "Material, espessura, canal e valor da dedução são obrigatórios.",
                             parent=form_ui.deducao_form)
        return

    nova_deducao_valor = float(form_ui.deducao_valor_entry.get().replace(',', '.'))
    espessura_obj = session.query(Espessura).filter_by(valor=espessura_valor).first()
    canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()
    material_obj = session.query(Material).filter_by(nome=material_nome).first()

    deducao_existente = session.query(Deducao).filter_by(
        espessura_id=espessura_obj.id,
        canal_id=canal_obj.id,
        material_id=material_obj.id
    ).first()

    if deducao_existente:
        messagebox.showerror("Erro", "Dedução já existe no banco de dados.")
        return

    nova_deducao = Deducao(
        espessura_id=espessura_obj.id,
        canal_id=canal_obj.id,
        material_id=material_obj.id,
        valor=nova_deducao_valor,
        observacao=nova_observacao_valor,
        forca=nova_forca_valor if nova_forca_valor else None
    )
    salvar_no_banco(nova_deducao, 'dedução',
                    f'espessura: {espessura_valor}, '
                    f'canal: {canal_valor}, '
                    f'material: {material_nome}, '
                    f'valor: {nova_deducao_valor}', form_ui)

def adicionar_espessura(form_ui):
    '''
    Lógica para adicionar uma nova espessura.
    '''
    espessura_valor = form_ui.espessura_valor_entry.get().replace(',', '.')
    if not re.match(r'^\d+(\.\d+)?$', espessura_valor):
        messagebox.showwarning("Atenção!",
                               "A espessura deve conter apenas números ou números decimais.",
                               parent=form_ui.espessura_form)
        form_ui.espessura_valor_entry.delete(0, tk.END)
        return

    espessura_existente = session.query(Espessura).filter_by(valor=espessura_valor).first()
    if espessura_existente:
        messagebox.showerror("Erro", "Espessura já existe no banco de dados.",
                             parent=form_ui.espessura_form)
        return

    nova_espessura = Espessura(valor=espessura_valor)
    salvar_no_banco(nova_espessura, 'espessura', f'valor: {espessura_valor}', form_ui)

def adicionar_material(form_ui):
    '''
    Lógica para adicionar um novo material.
    '''
    nome_material = form_ui.material_nome_entry.get()
    densidade_material = form_ui.material_densidade_entry.get()
    escoamento_material = form_ui.material_escoamento_entry.get()
    elasticidade_material = form_ui.material_elasticidade_entry.get()

    if not nome_material:
        messagebox.showerror("Erro", "O campo Material é obrigatório.", parent=form_ui.material_form)
        return

    material_existente = session.query(Material).filter_by(nome=nome_material).first()
    if material_existente:
        messagebox.showerror("Erro", "Material já existe no banco de dados.", parent=form_ui.material_form)
        return

    novo_material = Material(
        nome=nome_material,
        densidade=float(densidade_material) if densidade_material else None,
        escoamento=float(escoamento_material) if escoamento_material else None,
        elasticidade=float(elasticidade_material) if elasticidade_material else None
    )
    salvar_no_banco(novo_material,
                    'material',
                    f'nome: {nome_material}, '
                    f'densidade: {densidade_material}, '
                    f'escoamento: {escoamento_material}, '
                    f'elasticidade: {elasticidade_material}', form_ui)

def adicionar_canal(form_ui):
    '''
    Lógica para adicionar um novo canal.
    '''
    valor_canal = form_ui.canal_valor_entry.get()
    largura_canal = form_ui.canal_largura_entry.get()
    altura_canal = form_ui.canal_altura_entry.get()
    comprimento_total_canal = form_ui.canal_comprimento_entry.get()
    observacao_canal = form_ui.canal_observacao_entry.get()

    if not valor_canal:
        messagebox.showerror("Erro", "O campo Canal é obrigatório.", parent=form_ui.canal_form)
        return

    canal_existente = session.query(Canal).filter_by(valor=valor_canal).first()
    if canal_existente:
        messagebox.showerror("Erro", "Canal já existe no banco de dados.")
        return

    novo_canal = Canal(
        valor=valor_canal,
        largura=float(largura_canal) if largura_canal else None,
        altura=float(altura_canal) if altura_canal else None,
        comprimento_total=float(comprimento_total_canal) if comprimento_total_canal else None,
        observacao=observacao_canal if observacao_canal else None
    )
    salvar_no_banco(novo_canal,
                    'canal',
                    f'valor: {valor_canal}, '
                    f'largura: {largura_canal}, '
                    f'altura: {altura_canal}, '
                    f'comprimento_total: {comprimento_total_canal}, '
                    f'observacao: {observacao_canal}', form_ui)

def editar(tipo, form_ui, app_principal):
    '''
    Edita um item existente no banco de dados com base no tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''
    if not tem_permissao(tipo, 'editor', form_ui):
        return

    if not messagebox.askyesno("Confirmação", f"Tem certeza que deseja editar o(a) {tipo}?"):
        return

    configuracoes = obter_configuracoes(form_ui)
    config = configuracoes.get(tipo)
    
    if not config:
        messagebox.showerror("Erro", f"Configuração para '{tipo}' não encontrada.")
        return

    obj = item_selecionado(tipo, form_ui)
    if not obj:
        return
        
    obj_id = obj.id
    alteracoes = []  # Lista para armazenar as alterações
    
    for campo, entry in config['campos'].items():
        valor_novo = entry.get().strip()
        if valor_novo == "":
            valor_novo = None
        else:
            try:
                if campo in ["largura", "altura", "comprimento_total"]:
                    valor_novo = float(valor_novo.replace(",", "."))
            except ValueError:
                messagebox.showerror("Erro", f"Valor inválido para o campo '{campo}'.")
                return

        valor_antigo = getattr(obj, campo)
        if valor_antigo != valor_novo:  # Verifica se houve alteração
            alteracoes.append(f"{tipo} {campo}: '{valor_antigo}' -> '{valor_novo}'")
            setattr(obj, campo, valor_novo)

    tratativa_erro()
    detalhes = "; ".join(alteracoes)  # Concatena as alterações em uma string
    # Registrar a edição com detalhes
    registrar_log(g.USUARIO_NOME, "editar", tipo, obj_id, detalhes)
    messagebox.showinfo("Sucesso", f"{tipo.capitalize()} editado(a) com sucesso!")

    # Limpar os campos após a edição
    for entry in config['campos'].values():
        entry.delete(0, tk.END)

    limpar_campos(tipo, form_ui)
    listar(tipo, form_ui)
    atualizar_widgets(app_principal.cabecalho_ui, None, tipo)
    buscar(tipo, form_ui)

def excluir(tipo, form_ui, app_principal):
    '''
    Exclui um item do banco de dados com base no tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''
    if not tem_permissao(tipo, 'editor', form_ui):
        return

    configuracoes = obter_configuracoes(form_ui)
    config = configuracoes.get(tipo)
    
    if not config:
        messagebox.showerror("Erro", f"Configuração para '{tipo}' não encontrada.")
        return

    if not config['lista'].selection():
        messagebox.showerror("Erro", f"Nenhum {tipo} selecionado.")
        return

    aviso = messagebox.askyesno("Atenção!",
                                f"Ao excluir um(a) {tipo} todas as deduções relacionadas "
                                f"serão excluídas também, deseja continuar?",
                                parent=config['form'])
    if not aviso:
        return

    selected_item = config['lista'].selection()[0]
    item = config['lista'].item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(config['modelo']).filter_by(id=obj_id).first()
    
    if obj is None:
        messagebox.showerror("Erro",
                             f"{tipo.capitalize()} não encontrado(a).",
                             parent=config['form'])
        return

    # Excluir deduções relacionadas apenas se não for uma dedução
    if tipo != 'dedução':
        deducao_objs = (
            session.query(Deducao)
            .join(Canal, Deducao.canal_id == Canal.id)
            .filter(Canal.id == obj.id)
            .all()
        )

        for d in deducao_objs:
            session.delete(d)

    session.delete(obj)
    tratativa_erro()
    
    # Registrar a exclusão
    registrar_log(g.USUARIO_NOME,
                  "excluir",
                  tipo,
                  obj_id,
                  f"Excluído(a) {tipo} {(obj.nome) if tipo =='material' else obj.valor}")
    
    config['lista'].delete(selected_item)
    messagebox.showinfo("Sucesso",
                         f"{tipo.capitalize()} excluído(a) com sucesso!",
                         parent=config['form'])

    limpar_campos(tipo, form_ui)
    listar(tipo, form_ui)
    atualizar_widgets(app_principal.cabecalho_ui, None, tipo)

def preencher_campos(tipo, form_ui):
    '''
    Preenche os campos de entrada com os dados do item selecionado na lista.
    '''
    configuracoes = obter_configuracoes(form_ui)
    config = configuracoes.get(tipo)
    
    if not config:
        return

    obj = item_selecionado(tipo, form_ui)

    if obj:
        for campo, entry in config['campos'].items():
            entry.delete(0, tk.END)
            if getattr(obj, campo) is not None:
                entry.insert(0, getattr(obj, campo))
            else:
                entry.insert(0, '')

def limpar_campos(tipo, ui):
    '''
    Limpa os campos de entrada na aba correspondente ao tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''
    configuracoes = obter_configuracoes(ui)
    config = configuracoes.get(tipo)
    
    if not config:
        return

    for entry in config['campos'].values():
        entry.delete(0, tk.END)

def item_selecionado(tipo, ui):
    '''
    Retorna o objeto selecionado na lista correspondente ao tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''
    configuracoes = obter_configuracoes(ui)
    config = configuracoes.get(tipo)
    
    if not config:
        messagebox.showerror("Erro", f"Configuração para '{tipo}' não encontrada.")
        return None

    if not config['lista'].selection():
        messagebox.showerror("Erro", f"Nenhum {tipo} selecionado.")
        return None

    selected_item = config['lista'].selection()[0]
    item = config['lista'].item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(config['modelo']).filter_by(id=obj_id).first()

    return obj

def buscar(tipo, ui):
    '''
    Realiza a busca de itens no banco de dados com base nos critérios especificados.
    '''
    configuracoes = obter_configuracoes(ui)
    config = configuracoes.get(tipo)

    if not config:
        messagebox.showerror("Erro", f"Tipo '{tipo}' não encontrado nas configurações.")
        return

    if tipo != 'dedução' and (config.get('busca') is None or not config['busca'].winfo_exists()):
        return

    if config['lista'] is None or not config['lista'].winfo_exists():
        return

    def filtrar_deducoes(material_nome, espessura_valor, canal_valor):
        query = session.query(Deducao).join(Material).join(Espessura).join(Canal)

        if material_nome:
            query = query.filter(Material.nome == material_nome)
        if espessura_valor:
            query = query.filter(Espessura.valor == espessura_valor)
        if canal_valor:
            query = query.filter(Canal.valor == canal_valor)

        return query.all()

    if tipo == 'dedução':
        material_nome = config['entries']['material_combo'].get()
        espessura_valor = config['entries']['espessura_combo'].get()
        canal_valor = config['entries']['canal_combo'].get()
        itens = filtrar_deducoes(material_nome, espessura_valor, canal_valor)
    else:
        item = config['busca'].get().replace(',', '.') if config.get('busca') else ""
        if not item:
            listar(tipo, ui)
            return
        itens = session.query(config['modelo']).filter(config['campo_busca'].like(f"{item}%"))

    for item in config['lista'].get_children():
        config['lista'].delete(item)

    for item in itens:
        config['lista'].insert("", "end", values=config['valores'](item))
