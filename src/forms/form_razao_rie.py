"""
Módulo para exibir o formulário de cálculo de razão raio interno / espessura.
"""


from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGridLayout,
                               QLabel, QTreeWidget,
                               QTreeWidgetItem, QWidget, QTextBrowser)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.utils.janelas import (aplicar_no_topo, posicionar_janela)
from src.utils.utilitarios import obter_caminho_icone
from src.utils.calculos import razao_ri_espessura
from src.utils.interface import aplicar_medida_borda_espaco
from src.config import globals as g
from src.components.barra_titulo import BarraTitulo
from src.utils.estilo import obter_tema_atual


def main(root):
    """
    Inicializa e exibe o formulário de cálculo de razão raio interno /
    espessura com barra de título customizada.
    """
    _fechar_form_antigo()
    _criar_form(root)
    layout = _criar_layout_principal(g.RIE_FORM)
    _criar_barra_titulo(layout)
    conteudo = _criar_conteudo()
    layout.addWidget(conteudo)
    g.RIE_FORM.show()


def _fechar_form_antigo():
    if getattr(g, 'RIE_FORM', None):
        g.RIE_FORM.close()


def _criar_form(root):
    g.RIE_FORM = QDialog(root)
    g.RIE_FORM.setWindowTitle("Raio Interno / Espessura")
    g.RIE_FORM.setFixedSize(240, 280)
    g.RIE_FORM.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
    icone_path = obter_caminho_icone()
    g.RIE_FORM.setWindowIcon(QIcon(icone_path))
    aplicar_no_topo(g.RIE_FORM)
    posicionar_janela(g.RIE_FORM, None)


def _criar_layout_principal(parent):
    layout = QVBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout


def _criar_barra_titulo(layout):
    barra = BarraTitulo(g.RIE_FORM, tema=obter_tema_atual())
    barra.titulo.setText("Raio Interno / Espessura")
    layout.addWidget(barra)
    return barra


def _criar_conteudo():
    conteudo = QWidget()
    conteudo_layout = QVBoxLayout(conteudo)
    aplicar_medida_borda_espaco(conteudo_layout)
    main_frame = _criar_main_frame()
    conteudo_layout.addWidget(main_frame)
    conteudo.setLayout(conteudo_layout)
    return conteudo


def _criar_main_frame():
    main_frame = QWidget()
    main_layout = QGridLayout(main_frame)
    main_layout.setRowStretch(0, 0)
    main_layout.setRowStretch(1, 1)
    main_layout.setRowStretch(2, 0)
    _criar_label_razao(main_layout)
    _criar_label_resultado(main_layout)
    _criar_tabela(main_layout)
    _criar_aviso(main_layout)
    return main_frame


def _criar_label_razao(main_layout):
    razao_label = QLabel('Razão Raio Interno / Espessura: ')
    main_layout.addWidget(razao_label, 0, 0)


def _criar_label_resultado(main_layout):
    g.RAZAO_RIE_LBL = QLabel("")
    g.RAZAO_RIE_LBL.setMinimumWidth(100)
    g.RAZAO_RIE_LBL.setFrameShape(QLabel.Shape.Panel)
    g.RAZAO_RIE_LBL.setFrameShadow(QLabel.Shadow.Sunken)
    g.RAZAO_RIE_LBL.setFixedHeight(20)
    g.RAZAO_RIE_LBL.setAlignment(Qt.AlignCenter)
    main_layout.addWidget(g.RAZAO_RIE_LBL, 0, 1)


def _criar_tabela(main_layout):
    razao_ri_espessura()
    _create_table(main_layout, g.RAIO_K)


def _create_table(parent_layout, data):
    tree = QTreeWidget()
    tree.setHeaderLabels(["Razão", "Fator K"])
    tree.setRootIsDecorated(False)
    tree.setColumnWidth(0, 100)
    tree.setColumnWidth(1, 100)
    try:
        if isinstance(data, dict):
            for razao, k in data.items():
                item = QTreeWidgetItem([str(razao), str(k)])
                tree.addTopLevelItem(item)
        elif (
            hasattr(data, '__getitem__')
            and len(data) > 0
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


def _criar_aviso(main_layout):
    aviso_browser = QTextBrowser()
    aviso_browser.setHtml("""
        <p style="text-align: justify; font-weight: bold; color: red; padding: 5px;">
            <strong>Atenção:</strong> Os valores apresentados na tabela são teóricos. 
            Utilize-os apenas na ausência de dados mais precisos.
        </p>
    """)
    aviso_browser.setMaximumHeight(70)
    aviso_browser.setMaximumWidth(220)
    aviso_browser.setFrameStyle(0)
    aviso_browser.setVerticalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    aviso_browser.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    main_layout.addWidget(aviso_browser, 2, 0, 1, 2)


if __name__ == "__main__":
    main(None)
