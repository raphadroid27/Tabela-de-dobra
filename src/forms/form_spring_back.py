"""
Formulário para o cálculo de Spring Back
"""

from PySide6.QtWidgets import (
    QMainWindow, QGridLayout, QLabel, QComboBox, QWidget, QApplication)

from src.models.models import Material
from src.utils.banco_dados import session
from src.config import globals as g

# Configuração do banco de dados


def create_spring_back_form():
    """Cria o formulário de Spring Back usando PySide6"""
    spring_back_form = QMainWindow()
    spring_back_form.setWindowTitle("Cálculo de Spring Back")

    central_widget = QWidget()
    spring_back_form.setCentralWidget(central_widget)

    layout = QGridLayout()
    central_widget.setLayout(layout)

    # Obtém os nomes dos materiais como strings a partir da consulta
    materiais = [str(material.nome)
                 for material in session.query(Material).all()]

    layout.addWidget(QLabel("Material:"), 0, 0)
    g.MAT_COMB = QComboBox()
    g.MAT_COMB.addItems(materiais)
    layout.addWidget(g.MAT_COMB, 1, 0)

    return spring_back_form


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    form = create_spring_back_form()
    form.show()
    sys.exit(app.exec())
