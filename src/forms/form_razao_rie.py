"""
Módulo para exibir o formulário de cálculo de razão raio interno / espessura.
"""
try:
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                                   QLabel, QFrame, QScrollArea, QTreeWidget, 
                                   QTreeWidgetItem, QWidget)
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon, QFont
except ImportError:
    # Fallback para PyQt6 se PySide6 não estiver disponível
    from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
                                 QLabel, QFrame, QScrollArea, QTreeWidget, 
                                 QTreeWidgetItem, QWidget)
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon, QFont

from src.utils.janelas import (no_topo, posicionar_janela)
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
    g.RIE_FORM.resize(240, 280)
    g.RIE_FORM.setFixedSize(240, 280)

    # Define o ícone
    icone_path = obter_caminho_icone()
    g.RIE_FORM.setWindowIcon(QIcon(icone_path))

    no_topo(g.RIE_FORM)
    posicionar_janela(g.RIE_FORM, None)

    # Layout principal
    layout = QVBoxLayout(g.RIE_FORM)
    layout.setContentsMargins(5, 5, 5, 5)
    layout.setSpacing(5)

    # Frame principal
    main_frame = QWidget()
    main_layout = QGridLayout(main_frame)

    # Label da razão
    razao_label = QLabel('Razão Raio Interno / Espessura: ')
    main_layout.addWidget(razao_label, 0, 0)
    
    g.RAZAO_RIE_LBL = QLabel("")
    g.RAZAO_RIE_LBL.setStyleSheet("border: 1px solid gray; background-color: white")
    g.RAZAO_RIE_LBL.setMinimumWidth(100)
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
    aviso_label = QLabel(
        'Atenção: Os valores apresentados na tabela são teóricos. '
        'Utilize-os apenas na ausência de dados mais precisos.'
    )
    font = QFont('Arial', 10)
    font.setBold(True)
    aviso_label.setFont(font)
    aviso_label.setStyleSheet("color: red;")
    aviso_label.setWordWrap(True)
    aviso_label.setMaximumWidth(220)
    main_layout.addWidget(aviso_label, 2, 0, 1, 2)

    layout.addWidget(main_frame)

    razao_ri_espessura()
    create_table(main_layout, g.RAIO_K)

    g.RIE_FORM.show()


if __name__ == "__main__":
    main(None)
