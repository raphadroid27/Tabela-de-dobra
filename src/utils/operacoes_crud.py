"""
Este módulo contém funções auxiliares para manipulação de dados no aplicativo de cálculo
de dobras. Inclui operações CRUD (Criar, Ler, Atualizar, Excluir) para os tipos de dados:
dedução, espessura, material e canal.
"""
import re
from PySide6.QtWidgets import QTreeWidgetItem
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
from src.utils.widget import OperationHelper, WidgetManager
from src.utils.utilitarios import (
    ask_yes_no, show_error, show_info, show_warning)


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

    # As chamadas de atualização agora são centralizadas aqui,
    # após a conclusão de qualquer operação de adição.
    _limpar_campos(tipo)
    listar(tipo)
    atualizar_widgets(tipo)  # Esta chamada agora aciona a atualização global
    buscar(tipo)


def adicionar_deducao():
    """
    Lógica para adicionar uma nova dedução.
    """
    is_valid, values = OperationHelper.validate_deducao_operation()
    if not is_valid:
        show_error(
            "Erro", "Interface não inicializada corretamente ou campos obrigatórios vazios.",
            parent=g.DEDUC_FORM)
        return

    espessura_valor = values['DED_ESPES_COMB']
    canal_valor = values['DED_CANAL_COMB']
    material_nome = values['DED_MATER_COMB']
    nova_deducao_valor = float(values['DED_VALOR_ENTRY'].replace(',', '.'))
    nova_observacao_valor = values.get('DED_OBSER_ENTRY', '')
    nova_forca_valor = values.get('DED_FORCA_ENTRY', '')

    espessura_obj = session.query(Espessura).filter_by(
        valor=espessura_valor).first()
    canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()
    material_obj = session.query(Material).filter_by(
        nome=material_nome).first()

    if not espessura_obj:
        show_error(
            "Erro", f"Espessura '{espessura_valor}' não encontrada no banco.")
        return
    if not canal_obj:
        show_error("Erro", f"Canal '{canal_valor}' não encontrado no banco.")
        return
    if not material_obj:
        show_error(
            "Erro", f"Material '{material_nome}' não encontrado no banco.")
        return

    deducao_existente = session.query(Deducao).filter_by(
        espessura_id=espessura_obj.id,
        canal_id=canal_obj.id,
        material_id=material_obj.id
    ).first()

    if deducao_existente:
        show_error("Erro", "Dedução já existe no banco de dados.")
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
    is_valid, values = OperationHelper.validate_espessura_operation()
    if not is_valid:
        show_error("Erro", "Campo de espessura não inicializado ou vazio.")
        return

    espessura_valor = values['ESP_VALOR_ENTRY'].replace(',', '.')
    if not re.match(r'^\d+(\.\d+)?$', espessura_valor):
        show_warning("Atenção!",
                     "A espessura deve conter apenas números ou números decimais.",
                     parent=g.ESPES_FORM)
        esp_entry = WidgetManager.safe_get_widget('ESP_VALOR_ENTRY')
        WidgetManager.clear_widget(esp_entry)
        return

    espessura_existente = session.query(
        Espessura).filter_by(valor=espessura_valor).first()
    if espessura_existente:
        show_error("Erro", "Espessura já existe no banco de dados.",
                   parent=g.ESPES_FORM)
        return

    nova_espessura = Espessura(valor=espessura_valor)
    salvar_no_banco(nova_espessura, 'espessura', f'valor: {espessura_valor}')


def adicionar_material():
    """
    Lógica para adicionar um novo material.
    """
    is_valid, values = OperationHelper.validate_material_operation()
    if not is_valid:
        show_error(
            "Erro", "Interface não inicializada corretamente ou campos obrigatórios vazios.")
        return

    nome_material = values['MAT_NOME_ENTRY']
    densidade_material = values.get('MAT_DENS_ENTRY', '')
    escoamento_material = values.get('MAT_ESCO_ENTRY', '')
    elasticidade_material = values.get('MAT_ELAS_ENTRY', '')

    material_existente = session.query(
        Material).filter_by(nome=nome_material).first()
    if material_existente:
        show_error("Erro", "Material já existe no banco de dados.",
                   parent=g.MATER_FORM)
        return

    novo_material = Material(
        nome=nome_material,
        densidade=float(densidade_material) if densidade_material else None,
        escoamento=float(escoamento_material) if escoamento_material else None,
        elasticidade=float(
            elasticidade_material) if elasticidade_material else None
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
    if (g.CANAL_VALOR_ENTRY is None or g.CANAL_LARGU_ENTRY is None or
        g.CANAL_ALTUR_ENTRY is None or g.CANAL_COMPR_ENTRY is None or
            g.CANAL_OBSER_ENTRY is None):
        show_error("Erro", "Interface não inicializada corretamente.")
        return

    valor_canal = g.CANAL_VALOR_ENTRY.text()
    largura_canal = g.CANAL_LARGU_ENTRY.text()
    altura_canal = g.CANAL_ALTUR_ENTRY.text()
    comprimento_total_canal = g.CANAL_COMPR_ENTRY.text()
    observacao_canal = g.CANAL_OBSER_ENTRY.text()

    if not valor_canal:
        show_error("Erro", "O campo Canal é obrigatório.")
        return

    canal_existente = session.query(Canal).filter_by(valor=valor_canal).first()
    if canal_existente:
        show_error("Erro", "Canal já existe no banco de dados.")
        return

    novo_canal = Canal(
        valor=valor_canal,
        largura=float(largura_canal) if largura_canal else None,
        altura=float(altura_canal) if altura_canal else None,
        comprimento_total=float(
            comprimento_total_canal) if comprimento_total_canal else None,
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

    valor_novo = entry.text().strip() if hasattr(
        entry, 'text') else entry.get().strip()
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
                show_error("Erro", f"Valor inválido para o campo '{campo}'.")
                return None

    valor_antigo = getattr(obj, campo)
    if valor_antigo != valor_novo:
        setattr(obj, campo, valor_novo)
        return [f"{tipo} {campo}: '{valor_antigo}' -> '{valor_novo}'"]

    return []


def _limpar_campos_edicao(config):
    """Limpa os campos após a edição."""
    for entry in config['campos'].values():
        if entry is not None:
            if hasattr(entry, 'clear'):
                entry.clear()


def editar(tipo):
    """
    Edita um item existente no banco de dados com base no tipo especificado.
    """
    if not tem_permissao(tipo, 'editor'):
        return

    if not ask_yes_no("Confirmação", f"Tem certeza que deseja editar o(a) {tipo}?"):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = _item_selecionado(tipo)
    if obj is None:
        show_error("Erro", "Nenhum item selecionado para editar.")
        return

    obj_id = obj.id
    alteracoes = []

    for campo, entry in config['campos'].items():
        resultado = _processar_campo_edicao(obj, campo, entry, tipo)
        if resultado is None:
            return
        alteracoes.extend(resultado)

    tratativa_erro()
    detalhes = "; ".join(alteracoes)

    registrar_log(g.USUARIO_NOME, "editar", tipo, obj_id, detalhes)
    show_info("Sucesso", f"{tipo.capitalize()} editado(a) com sucesso!")

    _limpar_campos_edicao(config)
    _limpar_campos(tipo)
    listar(tipo)
    atualizar_widgets(tipo)
    buscar(tipo)


def excluir(tipo):
    """
    Exclui um item do banco de dados com base no tipo especificado.
    """
    if not tem_permissao(tipo, 'editor'):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if config['lista'] is None:
        return

    selected_items = config['lista'].selectedItems()
    if not selected_items:
        show_error(
            "Erro", f"Nenhum {tipo} selecionado para exclusão.", parent=config['form'])
        return

    aviso = ask_yes_no("Atenção!",
                       f"Ao excluir um(a) {tipo} todas as deduções relacionadas "
                       f"serão excluídas também, deseja continuar?",
                       parent=config['form'])
    if not aviso:
        return

    obj = _item_selecionado(tipo)
    if obj is None:
        show_error("Erro",
                   f"{tipo.capitalize()} não encontrado(a).",
                   parent=config['form'])
        return

    if tipo != 'dedução':
        if tipo == 'canal':
            deducao_objs = session.query(Deducao).filter(
                Deducao.canal_id == obj.id).all()
        elif tipo == 'material':
            deducao_objs = session.query(Deducao).filter(
                Deducao.material_id == obj.id).all()
        elif tipo == 'espessura':
            deducao_objs = session.query(Deducao).filter(
                Deducao.espessura_id == obj.id).all()
        else:
            deducao_objs = []

        for d in deducao_objs:
            session.delete(d)

    session.delete(obj)
    tratativa_erro()

    registrar_log(g.USUARIO_NOME,
                  "excluir",
                  tipo,
                  obj.id,
                  f"Excluído(a) {tipo} {(obj.nome) if tipo == 'material' else obj.valor}")

    show_info("Sucesso",
              f"{tipo.capitalize()} excluído(a) com sucesso!",
              parent=config['form'])

    _limpar_campos(tipo)
    listar(tipo)
    atualizar_widgets(tipo)
    buscar(tipo)


def preencher_campos(tipo):
    """
    Preenche os campos de entrada com os dados do item selecionado na lista.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = _item_selecionado(tipo)

    if obj:
        for campo, entry in config['campos'].items():
            if hasattr(entry, 'clear'):
                entry.clear()
                if getattr(obj, campo) is not None:
                    valor = str(getattr(obj, campo))
                    if hasattr(entry, 'setText'):
                        entry.setText(valor)
                    elif hasattr(entry, 'setCurrentText'):
                        entry.setCurrentText(valor)
                else:
                    if hasattr(entry, 'setText'):
                        entry.setText('')


def _limpar_campos(tipo):
    """
    Limpa os campos de entrada na aba correspondente ao tipo especificado.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    for entry in config['campos'].values():
        if hasattr(entry, 'clear'):
            entry.clear()
        elif hasattr(entry, 'setText'):
            entry.setText('')


def _item_selecionado(tipo):
    """
    Retorna o objeto selecionado na lista correspondente ao tipo especificado.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    selected_items = config['lista'].selectedItems()
    if not selected_items:
        return None

    selected_item = selected_items[0]

    try:
        if tipo == 'dedução':
            material_nome = selected_item.text(0)
            espessura_texto = selected_item.text(1)
            canal_valor = selected_item.text(2)
            valor_texto = selected_item.text(3)

            try:
                espessura_valor = float(
                    espessura_texto) if espessura_texto else None
                valor_deducao = float(valor_texto) if valor_texto else None
            except ValueError:
                return None

            obj = session.query(config['modelo']).join(Material).join(Espessura).join(Canal).filter(
                Material.nome == material_nome,
                Espessura.valor == espessura_valor,
                Canal.valor == canal_valor,
                config['modelo'].valor == valor_deducao
            ).first()

        elif tipo == 'material':
            nome = selected_item.text(0)
            obj = session.query(config['modelo']).filter_by(nome=nome).first()

        elif tipo == 'canal':
            valor = selected_item.text(0)
            obj = session.query(config['modelo']).filter_by(
                valor=valor).first()

        elif tipo == 'espessura':
            valor_texto = selected_item.text(0)
            try:
                valor = float(valor_texto) if valor_texto else None
                obj = session.query(config['modelo']).filter_by(
                    valor=valor).first()
            except ValueError:
                return None

        else:
            show_error("Erro", f"Tipo '{tipo}' não suportado para seleção.")
            return None

        return obj

    except (AttributeError, ValueError, TypeError) as e:
        show_error("Erro", f"Erro ao buscar {tipo}: {str(e)}")
        return None


def buscar(tipo):
    """
    Realiza a busca de itens no banco de dados com base nos critérios especificados.
    """
    if _deve_ignorar_busca(tipo):
        return

    config = _obter_configuracao(tipo)
    if config is None or not _widgets_validos(config, tipo):
        return

    itens = _buscar_itens(tipo, config)
    if itens is None:
        return

    _preencher_lista(config, itens)


def _deve_ignorar_busca(tipo):
    if getattr(g, 'INTERFACE_RELOADING', False):
        return True
    if tipo == 'dedução' and (
        getattr(g, 'DEDUC_FORM', None)
        and g.DEDUC_FORM.isVisible()
        and getattr(g, 'UPDATING_DEDUCAO_COMBOS', False)
    ):
        return True
    return False


def _obter_configuracao(tipo):
    configuracoes = obter_configuracoes()
    config = configuracoes.get(tipo)
    if config is None:
        show_error("Erro", f"Configuração para '{tipo}' não encontrada.")
    return config


def _widgets_validos(config, tipo):
    if tipo != 'dedução':
        busca_widget = config.get('busca')
        if busca_widget is None or not hasattr(busca_widget, 'isVisible'):
            return False
    if config.get('lista') is None:
        return False
    return True


def _buscar_itens(tipo, config):
    if tipo == 'dedução':
        return _obter_itens_deducao(config)
    return _obter_itens_geral(config, tipo)


def _obter_itens_deducao(config):
    """
    Obtém e ordena os itens de dedução para a lista.
    A ordenação é feita pelo valor da dedução, conforme a configuração.
    """
    material = config['entries']['material_combo'].currentText()
    espessura = config['entries']['espessura_combo'].currentText()
    canal = config['entries']['canal_combo'].currentText()
    query = session.query(Deducao).join(Material).join(Espessura).join(Canal)
    if material:
        query = query.filter(Material.nome == material)
    if espessura:
        query = query.filter(Espessura.valor == espessura)
    if canal:
        query = query.filter(Canal.valor == canal)

    # Adiciona ordenação pelo valor da dedução, conforme a configuração
    query = query.order_by(Deducao.valor)

    return query.all()


def _obter_itens_geral(config, tipo):
    busca_widget = config['busca']
    termo = busca_widget.text().replace(
        ',', '.') if hasattr(busca_widget, 'text') else ""
    if not termo:
        listar(tipo)
        return None
    return session.query(config['modelo']).filter(
        config['campo_busca'].like(f"{termo}%")
    )


def _preencher_lista(config, itens):
    config['lista'].clear()
    for item in itens:
        valores = config['valores'](item)
        valores_str = [str(v) if v is not None else '' for v in valores]
        item_widget = QTreeWidgetItem(valores_str)
        config['lista'].addTopLevelItem(item_widget)
