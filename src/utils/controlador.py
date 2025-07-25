"""
Este módulo atua como uma camada de 'Handler' ou 'Controller'.
Ele é responsável por:
1. Receber eventos da interface do usuário (ex: cliques de botão).
2. Coletar dados dos widgets da UI.
3. Chamar as funções de lógica de dados no módulo `operacoes_crud`.
4. Processar os resultados retornados pela camada de dados.
5. Exibir feedback ao usuário (mensagens de sucesso/erro).
6. Orquestrar a atualização da UI (listar, limpar campos, etc.).
"""
from PySide6.QtWidgets import QTreeWidgetItem
from src.utils.banco_dados import (session,
                                   obter_configuracoes
                                   )
from src.utils import operacoes_crud
from src.utils.usuarios import logado, tem_permissao
from src.config import globals as g
from src.models.models import Espessura, Material, Canal, Deducao
from src.utils.interface import atualizar_widgets, listar
from src.utils.widget import WidgetManager
from src.utils.utilitarios import (
    ask_yes_no, show_error, show_info, show_warning)


def adicionar(tipo):
    """
    Handler principal para adicionar um novo item.
    Orquestra a coleta de dados da UI, chamada da lógica de dados e atualização da UI.
    """
    if not logado(tipo):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]
    campos_widgets = config.get('campos', {})

    # 1. Coletar dados da UI
    dados_para_criar = {
        campo: WidgetManager.get_widget_value(widget)
        for campo, widget in campos_widgets.items()
    }

    # Casos especiais para dedução, que usa comboboxes diferentes
    if tipo == 'dedução':
        dados_para_criar['material_nome'] = WidgetManager.get_widget_value(
            g.DED_MATER_COMB)
        dados_para_criar['espessura_valor'] = WidgetManager.get_widget_value(
            g.DED_ESPES_COMB)
        dados_para_criar['canal_valor'] = WidgetManager.get_widget_value(
            g.DED_CANAL_COMB)

    # 2. Chamar a lógica de dados apropriada
    sucesso, mensagem, _ = False, "Tipo de operação inválido.", None
    if tipo == 'dedução':
        sucesso, mensagem, _ = operacoes_crud.criar_deducao(dados_para_criar)
    elif tipo == 'espessura':
        sucesso, mensagem, _ = operacoes_crud.criar_espessura(
            dados_para_criar.get('valor', ''))
    elif tipo == 'material':
        sucesso, mensagem, _ = operacoes_crud.criar_material(dados_para_criar)
    elif tipo == 'canal':
        sucesso, mensagem, _ = operacoes_crud.criar_canal(dados_para_criar)

    # 3. Processar resultado e atualizar UI
    if sucesso:
        show_info("Sucesso", mensagem, parent=config.get('form'))
        _limpar_campos(tipo)
        listar(tipo)
        atualizar_widgets(tipo)
        buscar(tipo)
    else:
        show_error("Erro", mensagem, parent=config.get('form'))


def editar(tipo):
    """
    Handler para editar um item existente.
    """
    if not tem_permissao(tipo, 'editor'):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = _item_selecionado(tipo)
    if obj is None:
        show_warning("Aviso", "Nenhum item selecionado para editar.",
                     parent=config.get('form'))
        return

    mensagem_confirmacao = f"Tem certeza que deseja editar o(a) {tipo}?"
    if not ask_yes_no("Confirmação", mensagem_confirmacao, parent=config.get('form')):
        return

    # 1. Coletar dados dos campos de edição
    dados_para_editar = {
        campo: WidgetManager.get_widget_value(widget)
        for campo, widget in config.get('campos', {}).items()
        if WidgetManager.get_widget_value(widget)
    }

    if not dados_para_editar:
        show_info("Informação", "Nenhum campo foi alterado.",
                  parent=config.get('form'))
        return

    # 2. Chamar a lógica de dados
    sucesso, mensagem, _ = operacoes_crud.editar_objeto(
        obj, dados_para_editar)

    # 3. Processar resultado e atualizar UI
    if sucesso:
        show_info("Sucesso", mensagem, parent=config.get('form'))
        _limpar_campos(tipo)
        listar(tipo)
        atualizar_widgets(tipo)
        buscar(tipo)
    else:
        show_error("Erro", mensagem, parent=config.get('form'))


def excluir(tipo):
    """
    Handler para excluir um item.
    """
    if not tem_permissao(tipo, 'editor'):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = _item_selecionado(tipo)
    if obj is None:
        show_warning(
            "Aviso", f"Nenhum {tipo} selecionado para exclusão.", parent=config['form'])
        return

    aviso = ask_yes_no("Atenção!",
                       (f"Ao excluir um(a) {tipo}, todas as deduções relacionadas "
                        f"serão excluídas também. Deseja continuar?"),
                       parent=config['form'])
    if not aviso:
        return

    # Chamar a lógica de dados
    sucesso, mensagem = operacoes_crud.excluir_objeto(obj)

    # Processar resultado e atualizar UI
    if sucesso:
        show_info("Sucesso", mensagem, parent=config['form'])
        _limpar_campos(tipo)
        listar(tipo)
        atualizar_widgets(tipo)
        buscar(tipo)
    else:
        show_error("Erro", mensagem, parent=config['form'])


def preencher_campos(tipo):
    """
    Preenche os campos de entrada com os dados do item selecionado na lista.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = _item_selecionado(tipo)

    if obj:
        for campo, entry in config['campos'].items():
            valor = getattr(obj, campo, None)
            WidgetManager.set_widget_value(
                entry, str(valor) if valor is not None else '')


def _limpar_campos(tipo):
    """
    Limpa os campos de entrada na aba correspondente ao tipo especificado.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    for entry in config['campos'].values():
        WidgetManager.clear_widget(entry)


def _item_selecionado(tipo):
    """
    Retorna o objeto selecionado na lista correspondente ao tipo especificado.
    Refatorado para ter um único ponto de retorno.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]
    obj = None

    lista_widget = config.get('lista')
    if not lista_widget:
        return None

    selected_items = lista_widget.selectedItems()
    if not selected_items:
        return None

    selected_item = selected_items[0]

    try:
        if tipo == 'dedução':
            material_nome = selected_item.text(0)
            espessura_valor = float(selected_item.text(1))
            canal_valor = selected_item.text(2)
            obj = session.query(Deducao).join(Material).join(Espessura).join(Canal).filter(
                Material.nome == material_nome,
                Espessura.valor == espessura_valor,
                Canal.valor == canal_valor,
            ).first()

        # Correção R1705: "elif" desnecessário após return implícito
        if tipo == 'material':
            nome = selected_item.text(0)
            obj = session.query(Material).filter_by(nome=nome).first()

        if tipo == 'canal':
            valor = selected_item.text(0)
            obj = session.query(Canal).filter_by(valor=valor).first()

        if tipo == 'espessura':
            valor = float(selected_item.text(0))
            obj = session.query(Espessura).filter_by(valor=valor).first()

    except (AttributeError, ValueError, TypeError, IndexError) as e:
        show_error("Erro", f"Erro ao buscar item selecionado: {str(e)}")
        return None  # Retorna None em caso de erro

    return obj


def _buscar_deducoes(config):
    """Função auxiliar para buscar deduções, reduzindo variáveis locais em 'buscar'."""
    criterios = {
        'material': WidgetManager.get_widget_value(config['entries']['material_combo']),
        'espessura': WidgetManager.get_widget_value(config['entries']['espessura_combo']),
        'canal': WidgetManager.get_widget_value(config['entries']['canal_combo'])
    }
    query = session.query(Deducao).join(
        Material).join(Espessura).join(Canal)
    if criterios['material']:
        query = query.filter(Material.nome == criterios['material'])
    if criterios['espessura']:
        query = query.filter(Espessura.valor == float(criterios['espessura']))
    if criterios['canal']:
        query = query.filter(Canal.valor == criterios['canal'])

    return query.order_by(Deducao.valor).all()


def buscar(tipo):
    """
    Realiza a busca de itens no banco de dados com base nos critérios especificados.
    Refatorado para reduzir o número de variáveis locais.
    """
    if getattr(g, 'INTERFACE_RELOADING', False):
        return

    config = obter_configuracoes().get(tipo)
    if not config or not config.get('lista'):
        return

    lista_widget = config['lista']
    lista_widget.clear()

    itens = []
    if tipo == 'dedução':
        itens = _buscar_deducoes(config)
    else:
        busca_widget = config.get('busca')
        termo = WidgetManager.get_widget_value(busca_widget).replace(',', '.')
        if not termo:
            listar(tipo)
            return

        campo_busca = config.get('campo_busca')
        itens = session.query(config['modelo']).filter(
            campo_busca.like(f"{termo}%")
        ).all()

    # Preencher a lista com os resultados
    for item in itens:
        valores = config['valores'](item)
        valores_str = [str(v) if v is not None else '' for v in valores]
        item_widget = QTreeWidgetItem(valores_str)
        lista_widget.addTopLevelItem(item_widget)
