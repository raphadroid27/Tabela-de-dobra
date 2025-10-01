"""Este módulo atua como uma camada de 'Handler' ou 'Controller'.

Ele é responsável por:
1. Receber eventos da interface do usuário (ex: cliques de botão).
2. Coletar dados dos widgets da UI.
3. Chamar as funções de lógica de dados no módulo `operacoes_crud`.
4. Processar os resultados retornados pela camada de dados.
5. Exibir feedback ao usuário (mensagens de sucesso/erro).
6. Orquestrar a atualização da UI (listar, limpar campos, etc.).
"""

# pylint: disable=R0912,R0914

import logging
from typing import Dict

from PySide6.QtCore import QTimer
from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Canal, Espessura, Material
from src.utils import operacoes_crud
from src.utils.banco_dados import get_session
from src.utils.calculos import buscar_deducao_por_parametros
from src.utils.interface import (
    FormWidgetUpdater,
    WidgetUpdater,
    listar,
    obter_configuracoes,
)
from src.utils.usuarios import logado, tem_permissao
from src.utils.utilitarios import ask_yes_no, show_error, show_info, show_warning
from src.utils.widget import WidgetManager, append_row

_buscar_timers: Dict[str, QTimer] = {}


def buscar_debounced(tipo: str, delay_ms: int = None):
    """Agenda a busca com um pequeno atraso para evitar consultas a cada tecla."""
    timer = _buscar_timers.get(tipo)
    if not timer:
        timer = QTimer()
        timer.setSingleShot(True)
        _buscar_timers[tipo] = timer

    def _run():
        try:
            buscar(tipo)
        except (ValueError, SQLAlchemyError) as e:
            logging.error("Erro em buscar_debounced(%s): %s", tipo, e)

    try:
        timer.timeout.disconnect()
    except (TypeError, RuntimeError):
        pass
    timer.timeout.connect(_run)

    if delay_ms is None:
        delay = 50
    else:
        try:
            delay = max(0, int(delay_ms))
        except (ValueError, TypeError):
            delay = 50
    timer.start(delay)


def adicionar(tipo):
    """Adiciona um novo item do tipo especificado."""
    if not logado(tipo):
        return

    config = obter_configuracoes()[tipo]
    dados_para_criar = {
        campo: WidgetManager.get_widget_value(widget)
        for campo, widget in config.get("campos", {}).items()
    }

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
        WidgetUpdater().atualizar(tipo)
        buscar(tipo)
        if (
            tipo in ["material", "espessura", "canal"]
            and hasattr(g, "DEDUC_FORM")
            and g.DEDUC_FORM
        ):
            listar("dedução")
            FormWidgetUpdater().atualizar(["material", "espessura", "canal"])
    else:
        show_error("Erro", mensagem, parent=config.get("form"))


def editar(tipo):
    """Edita um item existente do tipo especificado."""
    if not tem_permissao(tipo, "editor"):
        return

    config = obter_configuracoes()[tipo]
    obj_id, obj_type = _obter_item_selecionado_info(tipo)

    if obj_id is None:
        show_warning(
            "Aviso", "Nenhum item selecionado para editar.", parent=config.get("form")
        )
        return

    if not ask_yes_no(
        "Confirmação",
        f"Tem certeza que deseja editar o(a) {tipo}?",
        parent=config.get("form"),
    ):
        return

    dados_para_editar = {
        campo: WidgetManager.get_widget_value(widget)
        for campo, widget in config.get("campos", {}).items()
    }

    sucesso, mensagem, _ = operacoes_crud.editar_objeto(
        obj_id, obj_type, dados_para_editar
    )

    if sucesso:
        if "Nenhuma alteração" not in mensagem:
            show_info("Sucesso", mensagem, parent=config.get("form"))
            _limpar_campos(tipo)
            listar(tipo)
            WidgetUpdater().atualizar(tipo)
            buscar(tipo)
            if (
                tipo in ["material", "espessura", "canal"]
                and hasattr(g, "DEDUC_FORM")
                and g.DEDUC_FORM
            ):
                listar("dedução")
                FormWidgetUpdater().atualizar(["material", "espessura", "canal"])
        else:
            show_info("Informação", mensagem, parent=config.get("form"))
    else:
        show_error("Erro", mensagem, parent=config.get("form"))


def excluir(tipo):
    """Handler para excluir um item."""
    if not tem_permissao(tipo, "editor"):
        return

    config = obter_configuracoes()[tipo]
    lista_widget = config.get("lista")
    current_row = lista_widget.currentRow()

    if current_row < 0:
        show_warning(
            "Aviso", f"Nenhum {tipo} selecionado para exclusão.", parent=config["form"]
        )
        return

    obj_id, obj_type = _obter_item_selecionado_info(tipo)

    if obj_id is None:
        show_error(
            "Erro",
            "O item selecionado não foi encontrado no banco de dados.",
            parent=config["form"],
        )
        return

    aviso_msg = (
        f"Ao excluir um(a) {tipo}, todas as deduções relacionadas serão excluídas também. "
        "Deseja continuar?"
        if tipo in ["material", "espessura", "canal"]
        else "Tem certeza que deseja excluir esta dedução?"
    )
    if not ask_yes_no("Atenção!", aviso_msg, parent=config["form"]):
        return

    sucesso, mensagem = operacoes_crud.excluir_objeto(obj_id, obj_type)

    if sucesso:
        show_info("Sucesso", mensagem, parent=config["form"])
        lista_widget.removeRow(current_row)
        _limpar_campos(tipo)
        WidgetUpdater().atualizar(tipo)
        if (
            tipo in ["material", "espessura", "canal"]
            and hasattr(g, "DEDUC_FORM")
            and g.DEDUC_FORM
        ):
            listar("dedução")
            FormWidgetUpdater().atualizar(["material", "espessura", "canal"])
    else:
        show_error("Erro", mensagem, parent=config.get("form"))


def preencher_campos(tipo):
    """Preenche os campos de entrada com os dados do item selecionado na lista."""
    config = obter_configuracoes()[tipo]
    obj_id, obj_type = _obter_item_selecionado_info(tipo)

    if obj_id:
        try:
            with get_session() as session:
                obj = session.get(obj_type, obj_id)
                if obj:
                    for campo, entry in config["campos"].items():
                        valor = getattr(obj, campo, None)
                        WidgetManager.set_widget_value(
                            entry, str(valor) if valor is not None else ""
                        )
        except SQLAlchemyError as e:
            show_error(
                "Erro de DB", f"Não foi possível buscar dados para preenchimento: {e}"
            )


def _limpar_campos(tipo):
    """Limpa os campos de entrada na aba correspondente ao tipo especificado."""
    config = obter_configuracoes()[tipo]
    for entry in config["campos"].values():
        WidgetManager.clear_widget(entry)


def _obter_item_selecionado_info(tipo):
    """Retorna o ID e o tipo do objeto selecionado na lista."""
    config = obter_configuracoes()[tipo]
    lista_widget = config.get("lista")
    if not lista_widget:
        return None, None

    current_row = lista_widget.currentRow()
    if current_row < 0:
        return None, None

    obj_type = config["modelo"]

    try:
        with get_session() as session:
            if tipo == "dedução":
                material_nome = lista_widget.item(current_row, 0).text()
                espessura_valor = float(lista_widget.item(current_row, 1).text())
                canal_valor = lista_widget.item(current_row, 2).text()
                obj = buscar_deducao_por_parametros(
                    session, material_nome, espessura_valor, canal_valor
                )
            else:
                identifier_item = lista_widget.item(current_row, 0)
                if not identifier_item:
                    return None, None
                identifier_val = identifier_item.text()
                if tipo in ["espessura"]:
                    identifier_val = float(identifier_val)
                obj = (
                    session.query(obj_type)
                    .filter(config["campo_busca"] == identifier_val)
                    .first()
                )

            return (obj.id, obj_type) if obj else (None, None)
    except (SQLAlchemyError, ValueError, IndexError, AttributeError) as e:
        show_error("Erro", f"Erro ao buscar item selecionado: {e}")
        return None, None


def buscar(tipo):
    """Realiza a busca de itens no banco de dados."""
    if getattr(g, "INTERFACE_RELOADING", False):
        return

    config = obter_configuracoes().get(tipo)
    if not config or not config.get("lista"):
        return

    table_widget = config["lista"]
    table_widget.setRowCount(0)

    try:
        with get_session() as session:
            query = session.query(config["modelo"])
            if tipo == "dedução":
                query = query.join(Material).join(Espessura).join(Canal)
                crit_mat = WidgetManager.get_widget_value(
                    config["entries"]["material_combo"]
                )
                crit_esp = WidgetManager.get_widget_value(
                    config["entries"]["espessura_combo"]
                )
                crit_can = WidgetManager.get_widget_value(
                    config["entries"]["canal_combo"]
                )

                if crit_mat:
                    query = query.filter(Material.nome == crit_mat)
                if crit_esp:
                    query = query.filter(Espessura.valor == float(crit_esp))
                if crit_can:
                    query = query.filter(Canal.valor == crit_can)
            else:
                termo = WidgetManager.get_widget_value(config.get("busca")).replace(
                    ",", "."
                )
                if termo:
                    query = query.filter(config["campo_busca"].like(f"{termo}%"))

            itens = query.order_by(config["ordem"]).all()
            for item in itens:
                if tipo == "dedução" and not all(
                    [item.material, item.espessura, item.canal]
                ):
                    continue
                valores = config["valores"](item)
                if valores is None:
                    continue

                append_row(table_widget, valores)
    except (SQLAlchemyError, ValueError) as e:
        show_error("Erro de Busca", f"Não foi possível realizar a busca: {e}")
