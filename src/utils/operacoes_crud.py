"""
Este módulo contém funções auxiliares para manipulação de dados no aplicativo de cálculo
de dobras. Inclui operações CRUD (Criar, Ler, Atualizar, Excluir) para os tipos de dados:
dedução, espessura, material e canal.
"""
import re

from PySide6.QtWidgets import QMessageBox, QTreeWidgetItem

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
from src.utils.widget_validator import OperationHelper
from src.utils.widget_manager import WidgetManager


def show_error(title, message, parent=None):
    """Mostra uma mensagem de erro usando QMessageBox"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_info(title, message, parent=None):
    """Mostra uma mensagem de informação usando QMessageBox"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def show_warning(title, message, parent=None):
    """Mostra uma mensagem de aviso usando QMessageBox"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def ask_yes_no(title, message, parent=None):
    """Pergunta sim/não usando QMessageBox"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Question)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    return msg.exec() == QMessageBox.Yes


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


def adicionar_deducao():
    """
    Lógica para adicionar uma nova dedução.
    Versão refatorada usando WidgetValidator.
    """

    # Validar widgets e obter valores
    is_valid, values = OperationHelper.validate_deducao_operation()
    if not is_valid:
        show_error(
            "Erro", "Interface não inicializada corretamente ou campos obrigatórios vazios.",
            parent=g.DEDUC_FORM)
        return

    # Extrair valores
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

    # Verificar se os objetos foram encontrados no banco
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

    # Atualizar interface após salvar
    limpar_campos('dedução')
    listar('dedução')
    atualizar_widgets('dedução')


def adicionar_espessura():
    """
    Lógica para adicionar uma nova espessura.
    Versão refatorada usando WidgetValidator.
    """

    # Validar widgets e obter valores
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

    # Atualizar interface após salvar
    limpar_campos('espessura')
    listar('espessura')
    atualizar_widgets('espessura')


def adicionar_material():
    """
    Lógica para adicionar um novo material.
    Versão refatorada usando WidgetValidator.
    """

    # Validar widgets e obter valores
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

    # Atualizar interface após salvar
    limpar_campos('material')
    listar('material')
    atualizar_widgets('material')


def adicionar_canal():
    """
    Lógica para adicionar um novo canal.
    """
    # Verificar se os widgets foram inicializados
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

    # Atualizar interface após salvar
    limpar_campos('canal')
    listar('canal')
    atualizar_widgets('canal')


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
            if hasattr(entry, 'clear'):
                entry.clear()


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

    if not ask_yes_no("Confirmação", f"Tem certeza que deseja editar o(a) {tipo}?"):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = item_selecionado(tipo)
    if obj is None:
        show_error("Erro", "Nenhum item selecionado para editar.")
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
    show_info("Sucesso", f"{tipo.capitalize()} editado(a) com sucesso!")

    # Limpar campos e atualizar interface
    _limpar_campos_edicao(config, tipo)
    limpar_campos(tipo)
    listar(tipo)
    atualizar_widgets(tipo)


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

    # Verificar se há um item selecionado usando métodos do PySide6/Qt
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

    # Usar item_selecionado para buscar o objeto corretamente
    obj = item_selecionado(tipo)
    if obj is None:
        show_error("Erro",
                   f"{tipo.capitalize()} não encontrado(a).",
                   parent=config['form'])
        return

    # Excluir deduções relacionadas (apenas se não for do tipo dedução)
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

    # Excluir o objeto principal
    session.delete(obj)
    tratativa_erro()

    # Registrar a exclusão
    registrar_log(g.USUARIO_NOME,
                  "excluir",
                  tipo,
                  obj.id,
                  f"Excluído(a) {tipo} {(obj.nome) if tipo == 'material' else obj.valor}")

    show_info("Sucesso",
              f"{tipo.capitalize()} excluído(a) com sucesso!",
              parent=config['form'])

    # Atualizar interface após exclusão
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
            # Verificar se é QLineEdit ou QComboBox
            if hasattr(entry, 'clear'):
                entry.clear()
                if getattr(obj, campo) is not None:
                    valor = str(getattr(obj, campo))
                    if hasattr(entry, 'setText'):  # QLineEdit
                        entry.setText(valor)
                    elif hasattr(entry, 'setCurrentText'):  # QComboBox
                        entry.setCurrentText(valor)
                else:
                    if hasattr(entry, 'setText'):
                        entry.setText('')


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
        if hasattr(entry, 'clear'):
            entry.clear()
        elif hasattr(entry, 'setText'):
            entry.setText('')


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

    # Verificar se há um item selecionado no QTreeWidget
    selected_items = config['lista'].selectedItems()
    if not selected_items:
        # Retorna None silenciosamente quando não há seleção
        return None

    selected_item = selected_items[0]

    try:
        # Para QTreeWidget, precisamos obter o texto das colunas e buscar no banco
        # Como removemos o ID das colunas visíveis, vamos usar outros campos para identificar

        if tipo == 'dedução':
            # Para dedução: Material, Espessura, Canal, Valor, Observação, Força
            material_nome = selected_item.text(0)
            espessura_texto = selected_item.text(1)
            canal_valor = selected_item.text(2)
            valor_texto = selected_item.text(3)

            # Converter espessura e valor para float com tratamento de erro
            try:
                espessura_valor = float(
                    espessura_texto) if espessura_texto else None
                valor_deducao = float(valor_texto) if valor_texto else None
            except ValueError:
                # Retorna None silenciosamente se valores são inválidos
                return None

            # Buscar no banco usando os valores únicos
            obj = session.query(config['modelo']).join(Material).join(Espessura).join(Canal).filter(
                Material.nome == material_nome,
                Espessura.valor == espessura_valor,
                Canal.valor == canal_valor,
                config['modelo'].valor == valor_deducao
            ).first()

        elif tipo == 'material':
            # Para material: Nome, Densidade, Escoamento, Elasticidade
            nome = selected_item.text(0)
            obj = session.query(config['modelo']).filter_by(nome=nome).first()

        elif tipo == 'canal':
            # Para canal: Valor, Largura, Altura, Compr., Obs.
            valor = selected_item.text(0)
            obj = session.query(config['modelo']).filter_by(
                valor=valor).first()

        elif tipo == 'espessura':
            # Para espessura: Valor
            valor_texto = selected_item.text(0)
            try:
                valor = float(valor_texto) if valor_texto else None
                obj = session.query(config['modelo']).filter_by(
                    valor=valor).first()
            except ValueError:
                # Retorna None silenciosamente se valor é inválido
                return None

        else:
            show_error("Erro", f"Tipo '{tipo}' não suportado para seleção.")
            return None

        # Retorna o objeto se encontrado, None caso contrário (sem mostrar erro aqui)
        return obj

    except (AttributeError, ValueError, TypeError) as e:
        # Erro de programação ou tipo inválido - pode mostrar erro
        show_error("Erro", f"Erro ao buscar {tipo}: {str(e)}")
        return None


def buscar(tipo):
    """
    Realiza a busca de itens no banco de dados com base nos critérios especificados.
    """
    # Evitar busca durante recarregamento da interface
    if hasattr(globals.g, 'INTERFACE_RELOADING') and globals.g.INTERFACE_RELOADING:
        return

    # Evitar busca automática durante atualização dos comboboxes de dedução
    if (tipo == 'dedução' and hasattr(g, 'DEDUC_FORM') and g.DEDUC_FORM and
            g.DEDUC_FORM.isVisible() and hasattr(g, 'UPDATING_DEDUCAO_COMBOS')
            and g.UPDATING_DEDUCAO_COMBOS):
        return

    configuracoes = obter_configuracoes()

    try:
        config = configuracoes.get(tipo)
    except KeyError:
        show_error("Erro", f"Tipo '{tipo}' não encontrado nas configurações.")
        return

    # Verificar se config não é None
    if config is None:
        show_error("Erro", f"Configuração para '{tipo}' não encontrada.")
        return

    # Para QTreeWidget, verificar se o widget existe e está visível
    if tipo != 'dedução' and (config.get('busca') is None or not hasattr(config['busca'],
                                                                         'isVisible')):
        return

    if config['lista'] is None:
        return

    def filtrar_deducoes(material_nome, espessura_valor, canal_valor):
        query = session.query(Deducao).join(
            Material).join(Espessura).join(Canal)

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
        item = config['busca'].text().replace(',', '.') if config.get(
            'busca') and hasattr(config['busca'], 'text') else ""
        if not item:
            listar(tipo)
            return
        itens = session.query(config['modelo']).filter(
            config['campo_busca'].like(f"{item}%"))

    # Limpar a lista atual
    config['lista'].clear()

    # Adicionar os itens filtrados
    for item in itens:
        valores = config['valores'](item)
        # Garantir que todos os valores sejam strings
        valores_str = [str(v) if v is not None else '' for v in valores]
        item_widget = QTreeWidgetItem(valores_str)
        config['lista'].addTopLevelItem(item_widget)
