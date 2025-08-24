"""
Módulo para exibir o formulário de cálculo de razão raio interno / espessura.
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGridLayout,
    QLabel,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.components.barra_titulo import BarraTitulo
from src.config import globals as g
from src.utils.estilo import obter_tema_atual
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


class FormRazaoRIE:
    """Classe para o formulário de cálculo da razão raio interno / espessura."""

    def __init__(self):

        self.rie_form = QDialog(None)

    def show_form(self):
        """Exibe o formulário de cálculo da razão raio interno / espessura."""
        self._fechar_form_antigo()
        self._criar_form()
        layout = self._criar_layout_principal(self.rie_form)
        self._criar_barra_titulo(layout)
        conteudo = self._criar_conteudo()
        layout.addWidget(conteudo)
        self.rie_form.show()

    def _fechar_form_antigo(self):
        if self.rie_form is None:
            self.rie_form.close()

    def _criar_form(self):
        self.rie_form.setFixedSize(JANELA_LARGURA, JANELA_ALTURA)
        self.rie_form.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.rie_form.setWindowIcon(QIcon(ICON_PATH))
        Janela.posicionar_janela(self.rie_form, None)

    def _criar_layout_principal(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        return layout

    def _criar_barra_titulo(self, layout):
        barra = BarraTitulo(self.rie_form, tema=obter_tema_atual())
        barra.titulo.setText("Raio/Espessura")
        layout.addWidget(barra)
        return barra

    def _criar_conteudo(self):
        conteudo = QWidget()
        conteudo_layout = QVBoxLayout(conteudo)
        aplicar_medida_borda_espaco(conteudo_layout)
        main_frame = self._criar_main_frame()
        conteudo_layout.addWidget(main_frame)
        conteudo.setLayout(conteudo_layout)
        return conteudo

    def _criar_main_frame(self):
        main_frame = QWidget()
        main_layout = QGridLayout(main_frame)
        main_layout.setRowStretch(0, 0)
        main_layout.setRowStretch(1, 1)
        main_layout.setRowStretch(2, 0)
        self._criar_label_razao(main_layout)
        self._criar_label_resultado(main_layout)
        self._criar_tabela(main_layout)
        self._criar_aviso(main_layout)
        return main_frame

    def _criar_label_razao(self, main_layout):
        razao_label = QLabel("Razão Raio Interno / Espessura: ")
        main_layout.addWidget(razao_label, 0, 0)

    def _criar_label_resultado(self, main_layout):
        g.RAZAO_RIE_LBL = QLabel("")
        g.RAZAO_RIE_LBL.setMinimumWidth(COLUNA_RAZAO_LARGURA)
        g.RAZAO_RIE_LBL.setFrameShape(QLabel.Shape.Panel)
        g.RAZAO_RIE_LBL.setFrameShadow(QLabel.Shadow.Sunken)
        g.RAZAO_RIE_LBL.setFixedHeight(LABEL_ALTURA)
        g.RAZAO_RIE_LBL.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(g.RAZAO_RIE_LBL, 0, 1)

    def _criar_tabela(self, main_layout):
        calcular_valores()
        self._create_table(main_layout, g.RAIO_K)

    def _create_table(self, parent_layout, data):
        tree = QTreeWidget()
        tree.setHeaderLabels(["Razão", "Fator K"])
        tree.setRootIsDecorated(False)
        tree.setColumnWidth(0, COLUNA_RAZAO_LARGURA)
        tree.setColumnWidth(1, COLUNA_FATOR_K_LARGURA)
        try:
            if isinstance(data, dict):
                for razao, k in data.items():
                    item = QTreeWidgetItem([str(razao), str(k)])
                    tree.addTopLevelItem(item)
            elif (
                hasattr(data, "__getitem__")
                and data  # Pylint: usar truthiness ao invés de len() > 0
                and isinstance(data[0], (list, tuple))
                and len(data[0]) == 2
            ):
                for razao, k in data:
                    item = QTreeWidgetItem([str(razao), str(k)])
                    tree.addTopLevelItem(item)
            else:
                for valor in data:
                    item = QTreeWidgetItem([str(valor), ""])
                    tree.addTopLevelItem(item)
        except (TypeError, IndexError):
            item = QTreeWidgetItem([str(data), ""])
            tree.addTopLevelItem(item)
        parent_layout.addWidget(tree, 1, 0, 1, 2)

    def _criar_aviso(self, main_layout):
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
        main_layout.addWidget(aviso_browser, 2, 0, 1, 2)


def main(_):
    """
    Inicializa e exibe o formulário de cálculo de razão raio interno /
    espessura com barra de título customizada.
    """
    form = FormRazaoRIE()
    form.show_form()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main(None)
    sys.exit(app.exec())
