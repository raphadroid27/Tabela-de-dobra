"""
Módulo para exibir o formulário de cálculo de razão raio interno / espessura.
"""
try:
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                                   QLabel, QFrame, QScrollArea, QTreeWidget, 
                                   QTreeWidgetItem, QWidget, QTextBrowser)
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
except ImportError:
    # Fallback para PyQt6 se PySide6 não estiver disponível
    from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                                 QLabel, QFrame, QScrollArea, QTreeWidget, 
                                 QTreeWidgetItem, QWidget, QTextBrowser)
    from PyQt6.QtGui import QIcon

from src.utils.janelas import (aplicar_no_topo, posicionar_janela)
from src.utils.utilitarios import obter_caminho_icone
from src.utils.calculos import razao_ri_espessura
from src.config import globals as g


def main(root):
    """
    Inicializa e exibe o formulário de cálculo de razão raio interno / espessura.
    Configura a interface gráfica para exibir os valores e fatores K correspondentes.
    """
    if g.RIE_FORM:
        g.RIE_FORM.close()

    g.RIE_FORM = QDialog(root)
    g.RIE_FORM.setWindowTitle("Raio Interno / Espessura")
    g.RIE_FORM.setFixedSize(240, 280)

    # Define o ícone
    icone_path = obter_caminho_icone()
    g.RIE_FORM.setWindowIcon(QIcon(icone_path))

    aplicar_no_topo(g.RIE_FORM)
    posicionar_janela(g.RIE_FORM, None)

    # Layout principal
    layout = QVBoxLayout(g.RIE_FORM)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(5)

    # Frame principal
    main_frame = QWidget()
    main_layout = QGridLayout(main_frame)

    main_layout.setRowStretch(0, 0)
    main_layout.setRowStretch(1, 1)
    main_layout.setRowStretch(2, 0)

    # Label da razão
    razao_label = QLabel('Razão Raio Interno / Espessura: ')
    main_layout.addWidget(razao_label, 0, 0)
    
    g.RAZAO_RIE_LBL = QLabel("")
    g.RAZAO_RIE_LBL.setMinimumWidth(100)
    g.RAZAO_RIE_LBL.setFrameShape(QLabel.Shape.Panel)
    g.RAZAO_RIE_LBL.setFrameShadow(QLabel.Shadow.Sunken)
    g.RAZAO_RIE_LBL.setFixedHeight(20)  # Altura fixa
    g.RAZAO_RIE_LBL.setAlignment(Qt.AlignCenter)
    main_layout.addWidget(g.RAZAO_RIE_LBL, 0, 1)

    def create_table(parent_layout, data):
        # Criação da tabela
        tree = QTreeWidget()
        tree.setHeaderLabels(['Raio/Esp', 'Fator K'])
        tree.setRootIsDecorated(False)
        
        # Configurar larguras das colunas
        tree.setColumnWidth(0, 100)  # Raio/Esp
        tree.setColumnWidth(1, 100)  # Fator K

        # Inserção dos dados na tabela
        for raio, fator_k in data.items():
            item = QTreeWidgetItem([str(raio), str(fator_k)])
            tree.addTopLevelItem(item)

        parent_layout.addWidget(tree, 1, 0, 1, 2)  # span 2 columns

    # Aviso
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
    # Remover barras de rolagem e desabilitar rolagem
    aviso_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    aviso_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    main_layout.addWidget(aviso_browser, 2, 0, 1, 2)

    layout.addWidget(main_frame)

    razao_ri_espessura()
    create_table(main_layout, g.RAIO_K)

    g.RIE_FORM.show()


if __name__ == "__main__":
    main(None)
