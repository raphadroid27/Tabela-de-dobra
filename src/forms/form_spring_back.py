"""Formulário para o cálculo de Spring Back."""

import sys
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.components.barra_titulo import BarraTitulo
from src.config import globals as g
from src.forms.common.ui_helpers import configure_frameless_dialog
from src.models.models import Material
from src.utils.banco_dados import get_session
from src.utils.estilo import obter_tema_atual
from src.utils.utilitarios import ICON_PATH


def create_spring_back_form(root: Optional[QWidget] = None) -> QDialog:
    """Create the Spring Back form using QDialog with custom title bar."""
    form_spring = QDialog(root)
    form_spring.setWindowTitle("Cálculo de Spring Back")
    form_spring.setFixedSize(300, 150)
    configure_frameless_dialog(form_spring, ICON_PATH)

    # Layout vertical: barra de título customizada + conteúdo grid
    vlayout = QVBoxLayout(form_spring)
    vlayout.setContentsMargins(0, 0, 0, 0)
    vlayout.setSpacing(0)

    barra = BarraTitulo(form_spring, tema=obter_tema_atual())
    barra.titulo.setText("Cálculo de Spring Back")
    vlayout.addWidget(barra)

    conteudo = QWidget()
    layout = QGridLayout(conteudo)

    with get_session() as session:
        materiais = [str(material.nome) for material in session.query(Material).all()]

    layout.addWidget(QLabel("Material:"), 0, 0)
    g.MAT_COMB = QComboBox()
    g.MAT_COMB.addItems(materiais)
    layout.addWidget(g.MAT_COMB, 1, 0)

    conteudo.setLayout(layout)
    vlayout.addWidget(conteudo)

    return form_spring


if __name__ == "__main__":

    app = QApplication(sys.argv)
    form = create_spring_back_form()
    form.show()
    sys.exit(app.exec())
