"""Cria o frame de avisos na interface gráfica."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.utils.utilitarios import aplicar_medida_borda_espaco


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
        "3. Ferramenta 'bigode': fazer alívio de dobra em abas maiores que 20mm.",
    ]

    frame_avisos = QWidget()
    layout = QVBoxLayout(frame_avisos)

    for aviso in avisos_textos:
        aviso_label = QLabel(aviso)
        aviso_label.setObjectName("label_texto")
        aviso_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        aviso_label.setWordWrap(True)
        aviso_label.setMaximumWidth(300)
        layout.addWidget(aviso_label)

    aplicar_medida_borda_espaco(layout, 10)

    return frame_avisos
