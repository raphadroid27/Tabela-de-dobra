"""
Este módulo contém funções auxiliares para manipulação de dados no aplicativo de cálculo
de dobras. Inclui operações CRUD (Criar, Ler, Atualizar, Excluir) para os tipos de dados:
dedução, espessura, material e canal.
"""
import tkinter as tk
from tkinter import messagebox
import re
from src.utils.banco_dados import (session,
                                   salvar_no_banco,
                                   tratativa_erro,
                                   registrar_log,
                                   obter_configuracoes
                                   )
from src.utils.usuarios import logado, tem_permissao
from src.config import globals as g
from src.models.models import Espessura, Material, Canal, Deducao
from src.utils.interface import atualizar_widgets, listar


def adicionar(tipo):
    """
    Adiciona um novo item ao banco de dados com base no tipo especificado.
    """
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

    limpar_campos(tipo)
    listar(tipo)
    atualizar_widgets(tipo)
    buscar(tipo)


def adicionar_deducao():
    """
    Lógica para adicionar uma nova dedução.
    """
    # Verificar se os widgets foram inicializados
    if (g.DED_ESPES_COMB is None or g.DED_CANAL_COMB is None or
            g.DED_MATER_COMB is None or g.DED_VALOR_ENTRY is None):
        messagebox.showerror("Erro", "Interface não inicializada corretamente.")
        return

    espessura_valor = g.DED_ESPES_COMB.currentText()
    canal_valor = g.DED_CANAL_COMB.currentText()
    material_nome = g.DED_MATER_COMB.currentText()
    nova_observacao_valor = g.DED_OBSER_ENTRY.text() if g.DED_OBSER_ENTRY else ""
    nova_forca_valor = g.DED_FORCA_ENTRY.text() if g.DED_FORCA_ENTRY else ""

    if not all([espessura_valor, canal_valor, material_nome, g.DED_VALOR_ENTRY.text()]):
        messagebox.showerror("Erro",
                             "Material, espessura, canal e valor da dedução são obrigatórios.",
                             parent=g.DEDUC_FORM)
        return

    nova_deducao_valor = float(g.DED_VALOR_ENTRY.text().replace(',', '.'))

    espessura_obj = session.query(Espessura).filter_by(valor=espessura_valor).first()
    canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()
    material_obj = session.query(Material).filter_by(nome=material_nome).first()

    # Verificar se os objetos foram encontrados no banco
    if not espessura_obj:
        messagebox.showerror("Erro", f"Espessura '{espessura_valor}' não encontrada no banco.")
        return
    if not canal_obj:
        messagebox.showerror("Erro", f"Canal '{canal_valor}' não encontrado no banco.")
        return
    if not material_obj:
        messagebox.showerror("Erro", f"Material '{material_nome}' não encontrado no banco.")
        return

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
    """
    Lógica para adicionar uma nova espessura.
    """
    if g.ESP_VALOR_ENTRY is None:
        messagebox.showerror("Erro", "Campo de espessura não inicializado.")
        return

    espessura_valor = g.ESP_VALOR_ENTRY.text().replace(',', '.')
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
    """
    Lógica para adicionar um novo material.
    """
    # Verificar se os widgets foram inicializados
    if (g.MAT_NOME_ENTRY is None or g.MAT_DENS_ENTRY is None or
            g.MAT_ESCO_ENTRY is None or g.MAT_ELAS_ENTRY is None):
        messagebox.showerror("Erro", "Interface não inicializada corretamente.")
        return

    nome_material = g.MAT_NOME_ENTRY.text()
    densidade_material = g.MAT_DENS_ENTRY.text()
    escoamento_material = g.MAT_ESCO_ENTRY.text()
    elasticidade_material = g.MAT_ELAS_ENTRY.text()

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
    """
    Lógica para adicionar um novo canal.
    """
    # Verificar se os widgets foram inicializados
    if (g.CANAL_VALOR_ENTRY is None or g.CANAL_LARGU_ENTRY is None or
        g.CANAL_ALTUR_ENTRY is None or g.CANAL_COMPR_ENTRY is None or
            g.CANAL_OBSER_ENTRY is None):
        messagebox.showerror("Erro", "Interface não inicializada corretamente.")
        return

    valor_canal = g.CANAL_VALOR_ENTRY.text()
    largura_canal = g.CANAL_LARGU_ENTRY.text()
    altura_canal = g.CANAL_ALTUR_ENTRY.text()
    comprimento_total_canal = g.CANAL_COMPR_ENTRY.text()
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


def _processar_campo_edicao(obj, campo, entry, tipo):
    """Processa a edição de um campo individual."""
    if entry is None:
        return []

    valor_novo = entry.get().strip()
    if valor_novo == "":
        valor_novo = None
    else:
        campos_numericos = ["largura",
                            "altura",
                            "comprimento_total",
                            "valor",
                            "densidade",
                            "escoamento",
                            "elasticidade"
                            ]

        if campo in campos_numericos:
            try:
                valor_novo = float(valor_novo.replace(",", "."))
            except ValueError:
                messagebox.showerror("Erro", f"Valor inválido para o campo '{campo}'.")
                return None  # Indica erro

    valor_antigo = getattr(obj, campo)
    if valor_antigo != valor_novo:
        setattr(obj, campo, valor_novo)
        return [f"{tipo} {campo}: '{valor_antigo}' -> '{valor_novo}'"]

    return []


def _limpar_campos_edicao(config, tipo):
    """Limpa os campos após a edição."""
    for entry in config['campos'].values():
        if entry is not None:
            entry.delete(0, tk.END)


def editar(tipo):
    """
    Edita um item existente no banco de dados com base no tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    """
    if not tem_permissao(tipo, 'editor'):
        return

    if not messagebox.askyesno("Confirmação", f"Tem certeza que deseja editar o(a) {tipo}?"):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = item_selecionado(tipo)
    if obj is None:
        messagebox.showerror("Erro", "Nenhum item selecionado para editar.")
        return

    obj_id = obj.id
    alteracoes = []

    # Processar cada campo
    for campo, entry in config['campos'].items():
        resultado = _processar_campo_edicao(obj, campo, entry, tipo)
        if resultado is None:  # Erro de validação
            return
        alteracoes.extend(resultado)

    tratativa_erro()
    detalhes = "; ".join(alteracoes)

    # Registrar a edição com detalhes
    registrar_log(g.USUARIO_NOME, "editar", tipo, obj_id, detalhes)
    messagebox.showinfo("Sucesso", f"{tipo.capitalize()} editado(a) com sucesso!")

    # Limpar campos e atualizar interface
    _limpar_campos_edicao(config, tipo)
    limpar_campos(tipo)
    listar(tipo)
    atualizar_widgets(tipo)
    buscar(tipo)


def excluir(tipo):
    """
    Exclui um item do banco de dados com base no tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    """
    if not tem_permissao(tipo, 'editor'):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if config['lista'] is None:
        return

    aviso = messagebox.askyesno("Atenção!",
                                f"Ao excluir um(a) {tipo} todas as deduções relacionadas "
                                f"serão excluídas também, 'deseja continuar?",
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
                  f"Excluído(a) {tipo} {(obj.nome) if tipo == 'material' else obj.valor}")
    config['lista'].delete(selected_item)
    messagebox.showinfo("Sucesso",
                        f"{tipo.capitalize()} excluído(a) com sucesso!",
                        parent=config['form'])

    limpar_campos(tipo)
    listar(tipo)
    atualizar_widgets(tipo)


def preencher_campos(tipo):
    """
    Preenche os campos de entrada com os dados do item selecionado na lista.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = item_selecionado(tipo)

    if obj:
        for campo, entry in config['campos'].items():
            entry.delete(0, tk.END)
            if getattr(obj, campo) is not None:
                entry.insert(0, getattr(obj, campo))
            else:
                entry.insert(0, '')


def limpar_campos(tipo):
    """
    Limpa os campos de entrada na aba correspondente ao tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    for entry in config['campos'].values():
        entry.delete(0, tk.END)


def item_selecionado(tipo):
    """
    Retorna o objeto selecionado na lista correspondente ao tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if not config['lista'].selection():
        messagebox.showerror("Erro", f"Nenhum {tipo} selecionado.")
        return None

    selected_item = config['lista'].selection()[0]
    item = config['lista'].item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(config['modelo']).filter_by(id=obj_id).first()

    return obj


def buscar(tipo):
    """
    Realiza a busca de itens no banco de dados com base nos critérios especificados.
    """
    configuracoes = obter_configuracoes()

    try:
        config = configuracoes.get(tipo)
    except KeyError:
        messagebox.showerror("Erro", f"Tipo '{tipo}' não encontrado nas configurações.")
        return

    # Verificar se config não é None
    if config is None:
        messagebox.showerror("Erro", f"Configuração para '{tipo}' não encontrada.")
        return

    if tipo != 'dedução' and (config.get('busca') is None or not config['busca'].winfo_exists()):
        return

    if config['lista'] is None:
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
        material_nome = config['entries']['material_combo'].currentText()
        espessura_valor = config['entries']['espessura_combo'].currentText()
        canal_valor = config['entries']['canal_combo'].currentText()
        itens = filtrar_deducoes(material_nome, espessura_valor, canal_valor)
    else:
        item = config['busca'].text().replace(',', '.') if config.get('busca') else ""
        if not item:
            listar(tipo)
            return
        itens = session.query(config['modelo']).filter(config['campo_busca'].like(f"{item}%"))

    for item in config['lista'].get_children():
        config['lista'].delete(item)

    for item in itens:
        config['lista'].insert("", "end", values=config['valores'](item))
