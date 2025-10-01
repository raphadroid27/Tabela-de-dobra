"""Módulo para exibir o formulário de cálculo de razão raio interno/espessura."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QGridLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.components.barra_titulo import BarraTitulo
from src.config import globals as g
from src.forms.common.form_manager import BaseSingletonFormManager
from src.forms.common.ui_helpers import configure_frameless_dialog
from src.utils.estilo import aplicar_estilo_table_widget, obter_tema_atual
from src.utils.interface import calcular_valores
from src.utils.janelas import Janela
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco

# Constantes para configuração da interface
JANELA_LARGURA = 240
JANELA_ALTURA = 280
LABEL_ALTURA = 20
COLUNA_RAZAO_LARGURA = 100
COLUNA_FATOR_K_LARGURA = 100
AVISO_ALTURA_MAXIMA = 70
AVISO_LARGURA_MAXIMA = 220


class FormRazaoRIE(QDialog):
    """Formulário para cálculo da razão raio interno/espessura."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Raio/Espessura")
        self.setFixedSize(JANELA_LARGURA, JANELA_ALTURA)
        configure_frameless_dialog(self, ICON_PATH)
        Janela.posicionar_janela(self, None)

        layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(layout, 0)

        barra = BarraTitulo(self, tema=obter_tema_atual())
        barra.titulo.setText("Raio/Espessura")
        layout.addWidget(barra)

        conteudo = QWidget()
        conteudo_layout = QVBoxLayout(conteudo)
        aplicar_medida_borda_espaco(conteudo_layout, 0)
        conteudo_layout.addWidget(self._criar_main_frame())
        layout.addWidget(conteudo)

    def _criar_main_frame(self) -> QWidget:
        frame = QWidget()
        main_layout = QGridLayout(frame)
        main_layout.setRowStretch(0, 0)
        main_layout.setRowStretch(1, 1)
        main_layout.setRowStretch(2, 0)
        aplicar_medida_borda_espaco(main_layout, 10)

        main_layout.addWidget(QLabel("Raio Int. / Esp.: "), 0, 0)
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
        aplicar_estilo_table_widget(tabela)
        tabela.setAlternatingRowColors(True)
        tabela.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabela.verticalHeader().setVisible(False)

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
        aviso_browser.setMaximumWidth(AVISO_LARGURA_MAXIMA)
        aviso_browser.setFrameStyle(0)
        aviso_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        aviso_browser.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        return aviso_browser


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
