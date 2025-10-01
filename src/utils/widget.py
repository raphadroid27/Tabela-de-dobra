"""Módulo utilitário para gerenciamento, análise, criação e validação de widgets.

Inclui classes para análise de uso, factory, cache, operações e
gerenciamento de estado de widgets na aplicação. Também oferece funções para criar, registrar,
validar e manipular widgets usados em formulários e operações.
"""

import logging
from typing import Any, Callable, Dict, Iterable

from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)
from sqlalchemy.exc import SQLAlchemyError

import src.config.globals as g
from src.models.models import Canal, Espessura, Material
from src.utils.banco_dados import get_session
from src.utils.estilo import ALTURA_PADRAO_COMPONENTE
from src.utils.utilitarios import (
    WIDGETS_ENTRADA_CABECALHO,
    tem_configuracao_dobras_valida,
)

logger = logging.getLogger(__name__)


def append_row(table_widget: QTableWidget, values: Iterable[object]) -> None:
    """Insere uma nova linha com os valores fornecidos em um QTableWidget."""

    row_position = table_widget.rowCount()
    table_widget.insertRow(row_position)
    for col, value in enumerate(values):
        table_widget.setItem(
            row_position,
            col,
            QTableWidgetItem(str(value) if value is not None else ""),
        )


class WidgetFactory:
    """Factory para criação de widgets sob demanda."""

    _widget_creators: Dict[str, Callable] = {}

    @classmethod
    def register_creator(cls, widget_name: str, creator_func: Callable):
        """Registra uma função criadora para um tipo específico de widget."""
        cls._widget_creators[widget_name] = creator_func


class WidgetManager:
    """Gerenciador centralizado para operações com widgets."""

    @staticmethod
    def is_widget_valid(widget: QWidget) -> bool:
        """Verifica se um widget é válido."""
        if widget is None:
            return False
        try:
            widget.objectName()
            return True
        except RuntimeError:
            return False

    @staticmethod
    def get_widget_value(widget: QWidget, default: str = "") -> str:
        """Obtém o valor de um widget de forma segura."""
        if not WidgetManager.is_widget_valid(widget):
            return default
        try:
            if hasattr(widget, "currentText"):
                return widget.currentText() or default
            if hasattr(widget, "text"):
                return widget.text() or default
            return default
        except (AttributeError, RuntimeError):
            return default

    @staticmethod
    def set_widget_value(widget: QWidget, value: str):
        """Define o valor de um widget de forma segura."""
        if not WidgetManager.is_widget_valid(widget):
            return
        try:
            if hasattr(widget, "setCurrentText"):
                widget.setCurrentText(value)
            elif hasattr(widget, "setText"):
                widget.setText(value)
        except (AttributeError, RuntimeError):
            pass

    @staticmethod
    def clear_widget(widget: QWidget):
        """Limpa um widget de forma segura."""
        if not WidgetManager.is_widget_valid(widget):
            return
        try:
            if isinstance(widget, (QLineEdit, QComboBox)):
                widget.clear()
            elif isinstance(widget, QLabel):
                widget.setText("")
        except (AttributeError, RuntimeError):
            pass


class WidgetStateManager:
    """Gerenciador de estado dos widgets."""

    def __init__(self):
        self.widget_cache = {}
        self.is_enabled = True

    def enable(self):
        """Habilita o gerenciador de estado."""
        self.is_enabled = True

    def disable(self):
        """Desabilita o gerenciador de estado."""
        self.is_enabled = False

    def capture_current_state(self):
        """Captura o estado atual de todos os widgets relevantes."""
        if not self.is_enabled:
            return
        try:
            self._capture_cabecalho_state()
            self._capture_dobras_state()
        except (AttributeError, TypeError, RuntimeError):
            pass

    def _capture_cabecalho_state(self):
        self.widget_cache["cabecalho"] = {
            name: WidgetManager.get_widget_value(getattr(g, name, None))
            for name in WIDGETS_ENTRADA_CABECALHO
        }

    def _capture_dobras_state(self):
        if not tem_configuracao_dobras_valida():
            self.widget_cache["dobras"] = {}
            return

        dobras_state: Dict[str, Any] = {}
        for w in g.VALORES_W:
            for i in range(1, g.N):
                name = f"aba{i}_entry_{w}"
                dobras_state[name] = WidgetManager.get_widget_value(
                    getattr(g, name, None)
                )
        self.widget_cache["dobras"] = dobras_state

    def restore_widget_state(self):
        """Restaura o estado dos widgets a partir do cache."""
        if not self.is_enabled or not self.widget_cache:
            return
        try:
            self._restore_state("cabecalho")
            self._restore_state("dobras")
        except (AttributeError, TypeError, RuntimeError):
            pass

    def _restore_state(self, category: str):
        state = self.widget_cache.get(category, {})
        for name, value in state.items():
            if value:
                widget = getattr(g, name, None)
                WidgetManager.set_widget_value(widget, value)

    def get_cache_info(self):
        """Retorna informações sobre o cache atual."""
        cabecalho_count = len(self.widget_cache.get("cabecalho", {}))
        dobras_count = len(self.widget_cache.get("dobras", {}))
        return f"Cache: {cabecalho_count} widgets de cabeçalho, {dobras_count} widgets de dobras"


def _create_combo_base(height: int = ALTURA_PADRAO_COMPONENTE) -> QComboBox:
    combo = QComboBox()
    combo.setFixedHeight(height)
    return combo


def _create_entry_base(
    height: int = ALTURA_PADRAO_COMPONENTE, placeholder: str = ""
) -> QLineEdit:
    entry = QLineEdit()
    entry.setFixedHeight(height)
    if placeholder:
        entry.setPlaceholderText(placeholder)
    return entry


def _populate_combo_from_db(combo, query_func):
    try:
        with get_session() as session:
            items = query_func(session)
            combo.addItems(items)
    except (SQLAlchemyError, RuntimeError) as e:
        logger.error("Erro ao popular combobox do DB: %s", e)
    return combo


def create_deducao_material_combo():
    """Cria um combobox para seleção de material de dedução."""
    return _populate_combo_from_db(
        _create_combo_base(),
        lambda s: [m.nome for m in s.query(Material).order_by(Material.nome)],
    )


def create_deducao_espessura_combo():
    """Cria um combobox para seleção de espessura de dedução."""
    return _populate_combo_from_db(
        _create_combo_base(),
        lambda s: [
            str(v[0])
            for v in s.query(Espessura.valor).distinct().order_by(Espessura.valor)
        ],
    )


def create_deducao_canal_combo():
    """Cria um combobox para seleção de canal de dedução."""
    return _populate_combo_from_db(
        _create_combo_base(),
        lambda s: [
            str(v[0]) for v in s.query(Canal.valor).distinct().order_by(Canal.valor)
        ],
    )


def create_deducao_valor_entry():
    """Cria um campo de entrada para valor de dedução."""
    return _create_entry_base(placeholder="Digite o valor da dedução")


def create_deducao_observacao_entry():
    """Cria um campo de entrada para observação de dedução."""
    return _create_entry_base(placeholder="Observação (opcional)")


def create_deducao_forca_entry():
    """Cria um campo de entrada para força de dedução."""
    return _create_entry_base(placeholder="Força (opcional)")


WidgetFactory.register_creator("DED_MATER_COMB", create_deducao_material_combo)
WidgetFactory.register_creator("DED_ESPES_COMB", create_deducao_espessura_combo)
WidgetFactory.register_creator("DED_CANAL_COMB", create_deducao_canal_combo)
WidgetFactory.register_creator("DED_VALOR_ENTRY", create_deducao_valor_entry)
WidgetFactory.register_creator("DED_OBSER_ENTRY", create_deducao_observacao_entry)
WidgetFactory.register_creator("DED_FORCA_ENTRY", create_deducao_forca_entry)

widget_state_manager = WidgetStateManager()
