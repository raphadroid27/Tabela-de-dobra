'''
Funções auxiliares para o aplicativo de cálculo de dobras.
'''
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from math import pi
import re
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError
from models import Espessura, Material, Canal, Deducao, Usuario, Log
import globals as g
from funcoes import tem_permissao, atualizar_combobox

engine = create_engine('sqlite:///tabela_de_dobra.db')
session = sessionmaker(bind=engine)
session = session()

def adicionar(tipo):
    '''
    Adiciona um novo item ao banco de dados com base no tipo especificado.
    '''
    if not logado(tipo):
        return

    if tipo == 'dedução':
        adicionar_deducao()
    elif tipo == 'espessura':
        adicionar_espessura()
    elif tipo == 'material':
        adicionar_material()
    elif tipo == 'canal':
        adicionar_canal()


    atualizar_combobox(tipo)


def adicionar_deducao():
    '''
    Lógica para adicionar uma nova dedução.
    '''
    espessura_valor = g.DED_ESPES_COMB.get()
    canal_valor = g.DED_CANAL_COMB.get()
    material_nome = g.DED_MATER_COMB.get()
    nova_observacao_valor = g.DED_OBSER_ENTRY.get()
    nova_forca_valor = g.DED_FORCA_ENTRY.get()

    if not all([espessura_valor, canal_valor, material_nome, g.DED_VALOR_ENTRY.get()]):
        messagebox.showerror("Erro",
                             "Material, espessura, canal e valor da dedução são obrigatórios.")
        return

    nova_deducao_valor = float(g.DED_VALOR_ENTRY.get().replace(',', '.'))
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
                    f'valor: {nova_deducao_valor}')

def adicionar_espessura():
    '''
    Lógica para adicionar uma nova espessura.
    '''
    espessura_valor = g.ESP_VALOR_ENTRY.get().replace(',', '.')
    if not re.match(r'^\d+(\.\d+)?$', espessura_valor):
        messagebox.showwarning("Atenção!",
                               "A espessura deve conter apenas números ou números decimais.",
                               parent=g.ESPES_FORM)
        g.ESP_VALOR_ENTRY.delete(0, tk.END)
        return

    espessura_existente = session.query(Espessura).filter_by(valor=espessura_valor).first()
    if espessura_existente:
        messagebox.showerror("Erro", "Espessura já existe no banco de dados.",
                             parent=g.ESPES_FORM)
        return

    nova_espessura = Espessura(valor=espessura_valor)
    salvar_no_banco(nova_espessura, 'espessura', f'valor: {espessura_valor}')

def adicionar_material():
    '''
    Lógica para adicionar um novo material.
    '''
    nome_material = g.CONFIGURACOES['material']['entradas']['nome'].get()
    densidade_material = g.CONFIGURACOES['material']['entradas']['densidade'].get()
    escoamento_material = g.CONFIGURACOES['material']['entradas']['escoamento'].get()
    elasticidade_material = g.CONFIGURACOES['material']['entradas']['elasticidade'].get()

    if not nome_material:
        messagebox.showerror("Erro", "O campo Material é obrigatório.", parent=g.MATER_FORM)
        return

    material_existente = session.query(Material).filter_by(nome=nome_material).first()
    if material_existente:
        messagebox.showerror("Erro", "Material já existe no banco de dados.", parent=g.MATER_FORM)
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
                    f'elasticidade: {elasticidade_material}')

def adicionar_canal():
    '''
    Lógica para adicionar um novo canal.
    '''
    valor_canal = g.CANAL_VALOR_ENTRY.get()
    largura_canal = g.CANAL_LARGU_ENTRY.get()
    altura_canal = g.CANAL_ALTUR_ENTRY.get()
    comprimento_total_canal = g.CANAL_COMPR_ENTRY.get()
    observacao_canal = g.CANAL_OBSER_ENTRY.get()

    if not valor_canal:
        messagebox.showerror("Erro", "O campo Canal é obrigatório.")
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
                    f'observacao: {observacao_canal}')

def salvar_no_banco(obj, tipo, detalhes):
    '''
    Salva um objeto no banco de dados e registra o log.
    '''
    session.add(obj)
    tratativa_erro()
    registrar_log(g.USUARIO_NOME, 'adicionar', tipo, obj.id, f'{tipo} {detalhes}')

    config = g.CONFIGURACOES[tipo]

    messagebox.showinfo("Sucesso", f"Novo(a) {tipo} adicionado(a) com sucesso!")

def atualizar(tipo):
    '''
    Edita um item existente no banco de dados com base no tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''
    if not tem_permissao(tipo, 'editor'):  # Permitir que editores realizem esta ação
        return

    if not messagebox.askyesno("Confirmação", f"Tem certeza que deseja editar o(a) {tipo}?"):
        return

    
    config = g.CONFIGURACOES[tipo]

    obj = item_selecionado(tipo)
    obj_id = obj.id
    if obj:
        alteracoes = []  # Lista para armazenar as alterações
        for campo, entry in config['entradas'].items():
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
    else:
        messagebox.showerror("Erro", f"{tipo.capitalize()} não encontrado(a).")

    # Limpar os campos após a edição
    for entry in config['entradas'].values():
        entry.delete(0, tk.END)

    # Atualizar as listas e comboboxes

    atualizar_combobox(tipo)

def item_selecionado(tipo):
    '''
    Retorna o objeto selecionado na lista correspondente ao tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''

    config = g.CONFIGURACOES[tipo]

    if not config['lista'].selection():
        messagebox.showerror("Erro", f"Nenhum {tipo} selecionado.")
        return None

    selected_item = config['lista'].selection()[0]
    item = config['lista'].item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(config['modelo']).filter_by(id=obj_id).first()

    return obj

def excluir(tipo):
    '''
    Exclui um item do banco de dados com base no tipo especificado.
    Os tipos disponíveis são:]
    - dedução
    - espessura
    - material
    - canal
    '''
    if not tem_permissao(tipo,'editor'):  # Permitir que editores realizem esta ação
        return

    
    config = g.CONFIGURACOES[tipo]

    if config['lista'] is None:
        return

    aviso = messagebox.askyesno("Atenção!",
                                f"Ao excluir um(a) {tipo} todas as deduções relacionadas "
                                f"serão excluídas também, 'deseja continuar?")
    if not aviso:
        return

    selected_item = config['lista'].selection()[0]
    item = config['lista'].item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(config['modelo']).filter_by(id=obj_id).first()
    if obj is None:
        messagebox.showerror("Erro",
                             f"{tipo.capitalize()} não encontrado(a).")
        return

    deducao_objs = (
        session.query(Deducao)
        .join(Canal, Deducao.canal_id == Canal.id)  # Junção explícita entre Deducao e Canal
        .filter(Canal.id == obj.id)  # Filtrar pelo ID do objeto selecionado
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
                         f"{tipo.capitalize()} excluído(a) com sucesso!")

def tratativa_erro():
    '''
    Trata erros de integridade e operacionais no banco de dados.
    '''
    try:
        session.commit()
        print("Operação realizada com sucesso!")
    except IntegrityError as e:
        session.rollback()
        print(f"Erro de integridade no banco de dados: {e}")
    except OperationalError as e:
        session.rollback()
        print(f"Erro operacional no banco de dados: {e}")
    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
        raise

def registrar_log(usuario_nome, acao, tabela, registro_id, detalhes=None):
    '''
    Registra uma ação no banco de dados.
    '''
    log = Log(
        usuario_nome=usuario_nome,
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        detalhes=detalhes
    )
    session.add(log)
    tratativa_erro()
