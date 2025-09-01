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

from src.config import globals as g
from src.models.models import Canal, Deducao, Espessura, Material
from src.utils import operacoes_crud
from src.utils.banco_dados import Session

# --- INÍCIO DA ALTERAÇÃO ---
# A invalidação de cache agora é importada diretamente do gerenciador de cache.
from src.utils.interface import (
    atualizar_comboboxes_formulario,
    atualizar_widgets,
    listar,
    obter_configuracoes,
)

# --- FIM DA ALTERAÇÃO ---
from src.utils.usuarios import logado, tem_permissao
from src.utils.utilitarios import ask_yes_no, show_error, show_info, show_warning
from src.utils.widget import WidgetManager


def adicionar(tipo):
    """
    Handler principal para adicionar um novo item.
    Orquestra a coleta de dados da UI, chamada da lógica de dados e atualização da UI.
    """
    if not logado(tipo):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]
    campos_widgets = config.get("campos", {})

    # 1. Coletar dados da UI
    dados_para_criar = {
        campo: WidgetManager.get_widget_value(widget)
        for campo, widget in campos_widgets.items()
    }

    # Casos especiais para dedução, que usa comboboxes diferentes
    if tipo == "dedução":
        dados_para_criar["material_nome"] = WidgetManager.get_widget_value(
            g.DED_MATER_COMB
        )
        dados_para_criar["espessura_valor"] = WidgetManager.get_widget_value(
            g.DED_ESPES_COMB
        )
        dados_para_criar["canal_valor"] = WidgetManager.get_widget_value(
            g.DED_CANAL_COMB
        )

    # 2. Chamar a lógica de dados apropriada
    sucesso, mensagem, _ = False, "Tipo de operação inválido.", None
    if tipo == "dedução":
        sucesso, mensagem, _ = operacoes_crud.criar_deducao(dados_para_criar)
    elif tipo == "espessura":
        sucesso, mensagem, _ = operacoes_crud.criar_espessura(
            dados_para_criar.get("valor", "")
        )
    elif tipo == "material":
        sucesso, mensagem, _ = operacoes_crud.criar_material(dados_para_criar)
    elif tipo == "canal":
        sucesso, mensagem, _ = operacoes_crud.criar_canal(dados_para_criar)

    if sucesso:
        show_info("Sucesso", mensagem, parent=config.get("form"))

        _limpar_campos(tipo)
        listar(tipo)
        atualizar_widgets(tipo)
        buscar(tipo)

        # Atualiza o formulário de deduções se ele estiver aberto
        if tipo in ["material", "espessura", "canal"]:
            if hasattr(g, "DEDUC_FORM") and g.DEDUC_FORM:
                listar("dedução")
                atualizar_comboboxes_formulario(["material", "espessura", "canal"])

    else:
        show_error("Erro", mensagem, parent=config.get("form"))


def editar(tipo):
    """
    Handler para editar um item existente.
    """
    if not tem_permissao(tipo, "editor"):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = _item_selecionado(tipo)
    if obj is None:
        show_warning(
            "Aviso", "Nenhum item selecionado para editar.", parent=config.get("form")
        )
        return

    mensagem_confirmacao = f"Tem certeza que deseja editar o(a) {tipo}?"
    if not ask_yes_no("Confirmação", mensagem_confirmacao, parent=config.get("form")):
        return

    # CORREÇÃO: Coleta todos os campos do formulário, incluindo os vazios,
    # para permitir que a lógica de negócio em 'operacoes_crud' decida o que fazer.
    dados_para_editar = {
        campo: WidgetManager.get_widget_value(widget)
        for campo, widget in config.get("campos", {}).items()
    }

    sucesso, mensagem, _ = operacoes_crud.editar_objeto(obj, dados_para_editar)

    if sucesso:
        if mensagem != "Nenhuma alteração detectada.":
            show_info("Sucesso", mensagem, parent=config.get("form"))
            _limpar_campos(tipo)
            listar(tipo)
            atualizar_widgets(tipo)
            buscar(tipo)
            if tipo in ["material", "espessura", "canal"]:
                if hasattr(g, "DEDUC_FORM") and g.DEDUC_FORM:
                    listar("dedução")
                    atualizar_comboboxes_formulario(["material", "espessura", "canal"])
        else:
            show_info("Informação", mensagem, parent=config.get("form"))
    else:
        show_error("Erro", mensagem, parent=config.get("form"))


def excluir(tipo):
    """
    Handler para excluir um item.
    """
    if not tem_permissao(tipo, "editor"):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]
    lista_widget = config.get("lista")

    # Capturar o item do widget antes de buscar o objeto no DB
    selected_items = lista_widget.selectedItems()
    if not selected_items:
        show_warning(
            "Aviso", f"Nenhum {tipo} selecionado para exclusão.", parent=config["form"]
        )
        return

    item_widget_selecionado = selected_items[0]
    obj = _item_selecionado(tipo)  # Objeto do banco de dados

    if obj is None:
        show_error(
            "Erro",
            "O item selecionado não foi encontrado no banco de dados.",
            parent=config["form"],
        )
        return

    # A mensagem de aviso só faz sentido para material, espessura e canal
    if tipo in ["material", "espessura", "canal"]:
        aviso = ask_yes_no(
            "Atenção!",
            (
                f"Ao excluir um(a) {tipo}, todas as deduções relacionadas "
                f"serão excluídas também. Deseja continuar?"
            ),
            parent=config["form"],
        )
        if not aviso:
            return
    else:  # Para deduções, uma confirmação simples
        aviso = ask_yes_no(
            "Confirmação",
            "Tem certeza que deseja excluir esta dedução?",
            parent=config["form"],
        )
        if not aviso:
            return

    sucesso, mensagem = operacoes_crud.excluir_objeto(obj)

    if sucesso:
        show_info("Sucesso", mensagem, parent=config["form"])

        (
            item_widget_selecionado.parent() or lista_widget.invisibleRootItem()
        ).removeChild(item_widget_selecionado)

        _limpar_campos(tipo)
        atualizar_widgets(tipo)

        # Atualiza o formulário de deduções se ele estiver aberto
        if tipo in ["material", "espessura", "canal"]:
            if hasattr(g, "DEDUC_FORM") and g.DEDUC_FORM:
                listar("dedução")
                atualizar_comboboxes_formulario(["material", "espessura", "canal"])

    else:
        show_error("Erro", mensagem, parent=config.get("form"))


def preencher_campos(tipo):
    """
    Preenche os campos de entrada com os dados do item selecionado na lista.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = _item_selecionado(tipo)

    if obj:
        for campo, entry in config["campos"].items():
            valor = getattr(obj, campo, None)
            WidgetManager.set_widget_value(
                entry, str(valor) if valor is not None else ""
            )


def _limpar_campos(tipo):
    """
    Limpa os campos de entrada na aba correspondente ao tipo especificado.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    for entry in config["campos"].values():
        WidgetManager.clear_widget(entry)


def _item_selecionado(tipo):
    """
    Retorna o objeto selecionado na lista correspondente ao tipo especificado.
    Refatorado para ter um único ponto de retorno.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]
    obj = None

    lista_widget = config.get("lista")
    if not lista_widget:
        return None

    selected_items = lista_widget.selectedItems()
    if not selected_items:
        return None

    selected_item = selected_items[0]

    try:
        if tipo == "dedução":
            material_nome = selected_item.text(0)
            espessura_valor = float(selected_item.text(1))
            canal_valor = selected_item.text(2)
            obj = (
                Session.query(Deducao)
                .join(Material)
                .join(Espessura)
                .join(Canal)
                .filter(
                    Material.nome == material_nome,
                    Espessura.valor == espessura_valor,
                    Canal.valor == canal_valor,
                )
                .first()
            )
        elif tipo == "material":
            nome = selected_item.text(0)
            obj = Session.query(Material).filter_by(nome=nome).first()

        elif tipo == "canal":
            valor = selected_item.text(0)
            obj = Session.query(Canal).filter_by(valor=valor).first()

        elif tipo == "espessura":
            valor = float(selected_item.text(0))
            obj = Session.query(Espessura).filter_by(valor=valor).first()

    except (AttributeError, ValueError, TypeError, IndexError) as e:
        show_error("Erro", f"Erro ao buscar item selecionado: {str(e)}")
        return None

    return obj


def _buscar_deducoes(config):
    """Função auxiliar para buscar deduções, reduzindo variáveis locais em 'buscar'."""
    criterios = {
        "material": WidgetManager.get_widget_value(config["entries"]["material_combo"]),
        "espessura": WidgetManager.get_widget_value(
            config["entries"]["espessura_combo"]
        ),
        "canal": WidgetManager.get_widget_value(config["entries"]["canal_combo"]),
    }
    query = Session.query(Deducao).join(Material).join(Espessura).join(Canal)
    if criterios["material"]:
        query = query.filter(Material.nome == criterios["material"])
    if criterios["espessura"]:
        query = query.filter(Espessura.valor == float(criterios["espessura"]))
    if criterios["canal"]:
        query = query.filter(Canal.valor == criterios["canal"])

    return query.order_by(Deducao.valor).all()


def buscar(tipo):
    """
    Realiza a busca de itens no banco de dados com base nos critérios especificados.
    Refatorado para reduzir o número de variáveis locais.
    """
    if getattr(g, "INTERFACE_RELOADING", False):
        return

    config = obter_configuracoes().get(tipo)
    if not config or not config.get("lista"):
        return

    lista_widget = config["lista"]
    lista_widget.clear()

    itens = []
    if tipo == "dedução":
        itens = _buscar_deducoes(config)
    else:
        busca_widget = config.get("busca")
        termo = WidgetManager.get_widget_value(busca_widget).replace(",", ".")
        if not termo:
            listar(tipo)
            return

        campo_busca = config.get("campo_busca")
        itens = (
            Session.query(config["modelo"]).filter(campo_busca.like(f"{termo}%")).all()
        )

    # Preencher a lista com os resultados
    for item in itens:
        valores = config["valores"](item)
        valores_str = [str(v) if v is not None else "" for v in valores]
        item_widget = QTreeWidgetItem(valores_str)
        lista_widget.addTopLevelItem(item_widget)
