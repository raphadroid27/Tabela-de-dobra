"""Módulo para exibir o formulário de cálculo de razão raio interno/espessura."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QGridLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.config import globals as g
from src.forms.common import context_help
from src.forms.common.form_manager import BaseSingletonFormManager
from src.forms.common.ui_helpers import configurar_dialogo_padrao
from src.utils.estilo import aplicar_estilo_table_widget
from src.utils.themed_widgets import ThemedDialog
from src.utils.interface import calcular_valores
from src.utils.janelas import Janela
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco

# Constantes para configuração da interface
JANELA_LARGURA = 240
JANELA_ALTURA = 280
LABEL_ALTURA = 20
COLUNA_RAZAO_LARGURA = 100
COLUNA_FATOR_K_LARGURA = 100
AVISO_ALTURA_MAXIMA = 80


class FormRazaoRIE(ThemedDialog):
    """Formulário para cálculo da razão raio interno/espessura."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Raio/Espessura")
        self.setMinimumSize(JANELA_LARGURA, JANELA_ALTURA)
        self.resize(JANELA_LARGURA, JANELA_ALTURA)
        self.setMaximumSize(JANELA_LARGURA, 510)
        configurar_dialogo_padrao(self, ICON_PATH)
        Janela.posicionar_janela(self, None)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(layout, 0)

        conteudo = QWidget()
        conteudo_layout = QVBoxLayout(conteudo)
        aplicar_medida_borda_espaco(conteudo_layout, 0)
        conteudo_layout.addWidget(self._criar_main_frame())
        layout.addWidget(conteudo)

        # Adicionar atalho F1 para ajuda
        shortcut = QShortcut(QKeySequence("F1"), self)
        shortcut.activated.connect(self._mostrar_ajuda)

    def _criar_main_frame(self) -> QWidget:
        frame = QWidget()
        main_layout = QGridLayout(frame)
        main_layout.setRowStretch(0, 0)
        main_layout.setRowStretch(1, 1)
        main_layout.setRowStretch(2, 1)

        main_layout.setColumnStretch(0, 0)
        main_layout.setColumnStretch(1, 1)

        aplicar_medida_borda_espaco(main_layout, 10)

        label_razao = QLabel("Raio Int. / Esp.: ")
        label_razao.setObjectName("label_titulo")
        main_layout.addWidget(label_razao, 0, 0)
        main_layout.addWidget(self._criar_label_resultado(), 0, 1)
        main_layout.addWidget(self._criar_tabela(), 1, 0, 1, 2)
        main_layout.addWidget(self._criar_aviso(), 2, 0, 1, 2)
        return frame

    def _criar_label_resultado(self) -> QLabel:
        g.RAZAO_RIE_LBL = QLabel("")
        g.RAZAO_RIE_LBL.setMinimumWidth(COLUNA_RAZAO_LARGURA)
        g.RAZAO_RIE_LBL.setFrameShape(QLabel.Shape.Panel)
        g.RAZAO_RIE_LBL.setFrameShadow(QLabel.Shadow.Sunken)
        g.RAZAO_RIE_LBL.setFixedHeight(LABEL_ALTURA)
        g.RAZAO_RIE_LBL.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return g.RAZAO_RIE_LBL

    def _criar_tabela(self) -> QTableWidget:
        calcular_valores()
        tabela = QTableWidget()
        tabela.setColumnCount(2)
        tabela.setHorizontalHeaderLabels(["Razão", "Fator K"])
        tabela.setColumnWidth(0, COLUNA_RAZAO_LARGURA)
        tabela.setColumnWidth(1, COLUNA_FATOR_K_LARGURA)
        header = tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabela.setAlternatingRowColors(True)
        tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabela.verticalHeader().setVisible(False)

        aplicar_estilo_table_widget(tabela)

        dados = g.RAIO_K
        try:
            if isinstance(dados, dict):
                tabela.setRowCount(len(dados))
                for linha, (razao, k) in enumerate(dados.items()):
                    tabela.setItem(linha, 0, QTableWidgetItem(str(razao)))
                    tabela.setItem(linha, 1, QTableWidgetItem(str(k)))
            elif (
                hasattr(dados, "__getitem__")
                and dados
                and isinstance(dados[0], (list, tuple))
                and len(dados[0]) == 2
            ):
                tabela.setRowCount(len(dados))
                for linha, (razao, k) in enumerate(dados):
                    tabela.setItem(linha, 0, QTableWidgetItem(str(razao)))
                    tabela.setItem(linha, 1, QTableWidgetItem(str(k)))
            else:
                tabela.setRowCount(len(dados))
                for linha, valor in enumerate(dados):
                    tabela.setItem(linha, 0, QTableWidgetItem(str(valor)))
                    tabela.setItem(linha, 1, QTableWidgetItem(""))
        except (TypeError, IndexError):
            tabela.setRowCount(1)
            tabela.setItem(0, 0, QTableWidgetItem(str(dados)))
            tabela.setItem(0, 1, QTableWidgetItem(""))

        # Evitar seleção automática da primeira linha
        tabela.setCurrentCell(-1, -1)

        return tabela

    def _criar_aviso(self) -> QTextBrowser:
        aviso_browser = QTextBrowser()
        aviso_browser.setHtml(
            """
            <p style="text-align: justify; font-weight: bold; color: red; padding: 5px;">
                <strong>Atenção:</strong> Os valores apresentados na tabela são teóricos.
                Utilize-os apenas na ausência de dados mais precisos.
            </p>
        """
        )
        aviso_browser.setMaximumHeight(AVISO_ALTURA_MAXIMA)
        aviso_browser.setFrameStyle(0)
        aviso_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        aviso_browser.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        return aviso_browser

    def _mostrar_ajuda(self) -> None:
        """Mostra as instruções de ajuda para este formulário."""
        context_help.show_help("razao_rie", parent=self)


class FormManager(BaseSingletonFormManager):
    """Gerencia a instância do formulário para garantir unicidade."""

    FORM_CLASS = FormRazaoRIE


def main(parent=None):
    """Inicializa e exibe o formulário de razão raio interno/espessura."""
    FormManager.show_form(parent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main(None)
    sys.exit(app.exec())
