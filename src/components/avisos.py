"""
Módulo responsável por criar o frame de avisos na interface gráfica.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from src.utils.interface import aplicar_medida_borda_espaco


def avisos():
    """
    Cria um frame contendo avisos para o usuário.

    Args:
        root: O widget pai onde o frame será inserido.

    Returns:
        QWidget: O widget contendo os avisos.
    """
    avisos_textos = [
        "1. Xadrez → Laser sempre corta com a face xadrez para Baixo ↓.",
        "2. Corrugado → Laser sempre corta com a face do corrugado para Cima ↑.",
        "3. Ferramenta 'bigode': fazer alívio de dobra em abas maiores que 20mm."
    ]

    frame_avisos = QWidget()
    layout = QVBoxLayout(frame_avisos)

    font = QFont("Arial", 10)

    for aviso in avisos_textos:
        aviso_label = QLabel(aviso)
        aviso_label.setAlignment(Qt.AlignLeft)
        aviso_label.setFont(font)
        aviso_label.setWordWrap(True)
        aviso_label.setMaximumWidth(300)
        layout.addWidget(aviso_label)

    aplicar_medida_borda_espaco(layout)

    return frame_avisos
