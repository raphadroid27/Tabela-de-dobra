"""Cria o frame de avisos na interface gráfica."""

import logging
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
from sqlalchemy.exc import SQLAlchemyError

from src.models.models import Aviso
from src.utils.banco_dados import get_session
from src.utils.utilitarios import aplicar_medida_borda_espaco


class AvisosWidget(QWidget):
    """Widget que exibe os avisos, atualizável dinamicamente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_principal = QVBoxLayout(self)
        aplicar_medida_borda_espaco(self.layout_principal, 10)
        self.refresh()

    def refresh(self):
        """Recarrega os avisos do banco e reconstrói a UI."""
        # Limpa widgets anteriores
        while self.layout_principal.count():
            child = self.layout_principal.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        avisos_processados = []

        try:
            with get_session() as session:
                avisos_query = (
                    session.query(Aviso).filter_by(
                        ativo=True).order_by(Aviso.ordem).all()
                )
                if avisos_query:
                    for i, aviso in enumerate(avisos_query):
                        texto_limpo = re.sub(r"^\d+\.\s*", "", aviso.texto)
                        texto_numerado = f"{i + 1}. {texto_limpo}"
                        avisos_processados.append((texto_numerado, aviso.tamanho_fonte))
        except SQLAlchemyError as e:
            logging.error("Erro ao carregar avisos do banco de dados: %s", e)
            avisos_processados = []

        for texto_numerado, tamanho_fonte in avisos_processados:
            aviso_label = QLabel(texto_numerado)
            aviso_label.setObjectName("label_texto")
            aviso_label.setStyleSheet(f"font-size: {tamanho_fonte}pt;")
            aviso_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            aviso_label.setWordWrap(True)
            aviso_label.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            aviso_label.setTextFormat(Qt.TextFormat.RichText)
            self.layout_principal.addWidget(aviso_label)

        # Adiciona spacer no final para empurrar tudo para cima
        self.layout_principal.addStretch()


def avisos():
    """
    Função wrapper para manter compatibilidade, mas agora retorna a nova classe.
    Recomendado usar AvisosWidget diretamente.
    """
    return AvisosWidget()
