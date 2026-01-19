"""Cria o frame de avisos na interface gráfica."""

import logging
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from sqlalchemy.exc import SQLAlchemyError

from src.models.models import Aviso
from src.utils.banco_dados import get_session
from src.utils.utilitarios import aplicar_medida_borda_espaco


def avisos():
    """
    Cria um frame contendo avisos para o usuário.
    Carrega os avisos do banco de dados ou cria os padrões se não existirem.

    Returns:
        QWidget: O widget contendo os avisos.
    """
    frame_avisos = QWidget()
    layout = QVBoxLayout(frame_avisos)

    avisos_padrao = [
        "Xadrez → Laser sempre corta com a face xadrez para Baixo ↓.",
        "Corrugado → Laser sempre corta com a face do corrugado para Cima ↑.",
        "Ferramenta <b>'bigode'</b> → Adicionar alívio de dobra se "
        "abas <b><span style='color:red;'>maiores que 20mm</span></b>.",
    ]

    avisos_bd = []

    try:
        with get_session() as session:
            # Tenta buscar avisos ativos
            avisos_query = (
                session.query(Aviso).filter_by(ativo=True).order_by(Aviso.ordem).all()
            )

            if not avisos_query:
                # Se não houver avisos no banco, verifica se a tabela está vazia
                # para popular com os padrões (apenas na primeira vez)
                todos_avisos = session.query(Aviso).count()
                if todos_avisos == 0:
                    logging.info("Populando tabela de avisos com valores padrão.")
                    for index, texto in enumerate(avisos_padrao):
                        novo_aviso = Aviso(texto=texto, ordem=index, ativo=True)
                        session.add(novo_aviso)
                    session.commit()
                    # Recarrega após inserir
                    avisos_query = (
                        session.query(Aviso)
                        .filter_by(ativo=True)
                        .order_by(Aviso.ordem)
                        .all()
                    )

            if avisos_query:
                avisos_bd = [a.texto for a in avisos_query]

    except SQLAlchemyError as e:
        logging.error("Erro ao carregar avisos do banco de dados: %s", e)
        # Fallback para os avisos padrão em memória em caso de erro grave
        avisos_bd = avisos_padrao

    for i, aviso_texto in enumerate(avisos_bd):
        # Remove numeração explicita se existir no texto salvo (ex: "1. Texto")
        texto_limpo = re.sub(r"^\d+\.\s*", "", aviso_texto)
        texto_numerado = f"{i + 1}. {texto_limpo}"

        aviso_label = QLabel(texto_numerado)
        aviso_label.setObjectName("label_texto")
        aviso_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        aviso_label.setWordWrap(True)
        aviso_label.setMaximumWidth(300)
        # Permite uso de links/HTML rico
        aviso_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(aviso_label)

    aplicar_medida_borda_espaco(layout, 10)

    return frame_avisos
