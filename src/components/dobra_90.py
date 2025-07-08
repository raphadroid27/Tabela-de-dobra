"""
Este módulo contém funções para criar e gerenciar o frame de dobras
"""
from PySide6.QtWidgets import QGroupBox, QLabel, QLineEdit, QGridLayout
from PySide6.QtCore import Qt
from src.config import globals as g
from src.utils.interface import (
    calcular_dobra,
    copiar,
    focus_next_entry,
    focus_previous_entry
)

LARGURA = 12


def dobras(frame, w):
    """
    Cria o frame para as dobras, com base no valor de n.
    O frame é criado apenas uma vez, e os widgets são atualizados
    """
    g.FRAME_DOBRA = QGroupBox()
    layout = QGridLayout(g.FRAME_DOBRA)
    g.FRAME_DOBRA.setLayout(layout)

    # Configurar espaçamento e margens
    layout.setSpacing(5)
    layout.setContentsMargins(5, 5, 5, 5)

    # Configurar larguras das colunas para alinhamento com cabeçalho
    # Coluna 0: Labels "Aba:" - largura fixa
    layout.setColumnMinimumWidth(0, 30)
    layout.setColumnStretch(0, 0)  # Não expande

    # Colunas 1, 2, 3: Larguras iguais e expansíveis (mesmo que cabeçalho)
    for col in range(1, 4):
        layout.setColumnStretch(col, 1)  # Expande igualmente

    entradas_dobras(g.N, w)
    return g.FRAME_DOBRA


def entradas_dobras(valor, w):
    """
    Cria os widgets para as dobras, com base no valor de n.
    """
    # Limpar layout antigo
    if hasattr(g, 'FRAME_DOBRA') and g.FRAME_DOBRA.layout() is not None:
        while g.FRAME_DOBRA.layout().count():
            child = g.FRAME_DOBRA.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    # Atualizar o valor de n
    g.N = valor

    layout = g.FRAME_DOBRA.layout()

    # Adicionar widgets novamente
    labels = ['Medida Ext.', 'Medida Dobra', 'Metade Dobra']
    for i, label_text in enumerate(labels):
        header_label = QLabel(label_text)
        header_label.setFixedHeight(20)  # Altura fixa
        layout.addWidget(header_label, 0, i + 1)

    for i in range(1, g.N):
        aba_label = QLabel(f"Aba {i}:")
        aba_label.setFixedHeight(20)  # Altura fixa
        layout.addWidget(aba_label, i, 0)

        entry = QLineEdit()
        entry.setAlignment(Qt.AlignCenter)
        entry.setFixedHeight(20)  # Altura fixa
        setattr(g, f'aba{i}_entry_{w}', entry)
        layout.addWidget(entry, i, 1)
        entry.textChanged.connect(lambda text, w=w: calcular_dobra(w))
        entry.returnPressed.connect(lambda i=i, w=w: focus_next_entry(i, w))
        # Substituir keyPressEvent para lidar com UP/DOWN sem criar uma função separada
        def custom_key_press_event(event, entry=entry, i=i, w=w):
            if event.key() == Qt.Key_Down:
                focus_next_entry(i, w)
            elif event.key() == Qt.Key_Up:
                focus_previous_entry(i, w)
            else:
                QLineEdit.keyPressEvent(entry, event)

        entry.keyPressEvent = custom_key_press_event
        entry.setToolTip("Insira o valor da dobra.")

        medida_dobra_label = QLabel()
        medida_dobra_label.setFrameShape(QLabel.Shape.Panel)
        medida_dobra_label.setFrameShadow(QLabel.Shadow.Sunken)
        medida_dobra_label.setFixedHeight(20)  # Altura fixa
        medida_dobra_label.setAlignment(Qt.AlignCenter)
        setattr(g, f'medidadobra{i}_label_{w}', medida_dobra_label)
        layout.addWidget(medida_dobra_label, i, 2)
        medida_dobra_label.mousePressEvent = lambda event, i=i, w=w: copiar(
            'medida_dobra', i, w)
        medida_dobra_label.setToolTip("Clique para copiar a medida da dobra.")

        metade_dobra_label = QLabel()
        metade_dobra_label.setFrameShape(QLabel.Shape.Panel)
        metade_dobra_label.setFrameShadow(QLabel.Shadow.Sunken)
        metade_dobra_label.setFixedHeight(20)  # Altura fixa
        metade_dobra_label.setAlignment(Qt.AlignCenter)
        setattr(g, f'metadedobra{i}_label_{w}', metade_dobra_label)
        layout.addWidget(metade_dobra_label, i, 3)
        metade_dobra_label.mousePressEvent = lambda event, i=i, w=w: copiar(
            'metade_dobra', i, w)
        metade_dobra_label.setToolTip("Clique para copiar a metade da dobra.")

    blank_label = QLabel("Medida do Blank:")
    blank_label.setAlignment(Qt.AlignCenter)
    blank_label.setFixedHeight(20)  # Altura fixa
    layout.addWidget(blank_label, i + 1, 0, 1, 2)

    medida_blank = QLabel()
    medida_blank.setFrameShape(QLabel.Shape.Panel)
    medida_blank.setFrameShadow(QLabel.Shadow.Sunken)
    medida_blank.setFixedHeight(20)  # Altura fixa
    medida_blank.setAlignment(Qt.AlignCenter)
    setattr(g, f'medida_blank_label_{w}', medida_blank)
    layout.addWidget(medida_blank, i + 1, 2)
    medida_blank.mousePressEvent = lambda event, i=i, w=w: copiar(
        'blank', i, w)
    medida_blank.setToolTip("Clique para copiar a medida do blank.")

    metade_blank = QLabel()
    metade_blank.setFrameShape(QLabel.Shape.Panel)
    metade_blank.setFrameShadow(QLabel.Shadow.Sunken)
    metade_blank.setFixedHeight(20)  # Altura fixa
    metade_blank.setAlignment(Qt.AlignCenter)
    setattr(g, f'metade_blank_label_{w}', metade_blank)
    layout.addWidget(metade_blank, i + 1, 3)
    metade_blank.mousePressEvent = lambda event, i=i, w=w: copiar(
        'metade_blank', i, w)
    metade_blank.setToolTip("Clique para copiar a metade do blank.")
