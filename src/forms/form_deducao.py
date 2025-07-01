"""
# Formulário de Dedução
# Este módulo implementa o formulário de dedução, permitindo a adição, edição
# e exclusão de deduções. Ele utiliza a biblioteca PySide6 para a interface
# gráfica, o módulo globals para variáveis globais e o módulo funcoes para
# operações relacionadas ao banco de dados.
"""
try:
    from PySide6.QtWidgets import (QDialog, QGridLayout, 
                                   QGroupBox, QLabel, QComboBox, QPushButton, 
                                   QTreeWidget, QLineEdit)
    from PySide6.QtGui import QIcon
except ImportError:
    # Fallback para PyQt6 se PySide6 não estiver disponível
    from PyQt6.QtWidgets import (QDialog, QGridLayout, 
                                 QGroupBox, QLabel, QComboBox, QPushButton, 
                                 QTreeWidget, QLineEdit)
    from PyQt6.QtGui import QIcon
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.interface import (listar,
                                 limpar_busca,
                                 atualizar_widgets,
                                 configurar_main_frame
                                 )
from src.utils.utilitarios import obter_caminho_icone
from src.utils.operacoes_crud import (buscar,
                                      preencher_campos,
                                      excluir,
                                      editar,
                                      adicionar
                                      )
from src.config import globals as g


def configurar_janela(root):
    """
    Configura a janela principal do formulário de deduções.
    """
    if g.DEDUC_FORM:
        g.DEDUC_FORM.close()

    g.DEDUC_FORM = QDialog(root)
    g.DEDUC_FORM.setWindowTitle("Formulário de Deduções")
    g.DEDUC_FORM.resize(500, 420)
    g.DEDUC_FORM.setFixedSize(500, 420)

    icone_path = obter_caminho_icone()
    g.DEDUC_FORM.setWindowIcon(QIcon(icone_path))

    no_topo(g.DEDUC_FORM)
    posicionar_janela(g.DEDUC_FORM, None)


def criar_frame_busca(main_frame):
    """
    Cria o frame de busca.
    """
    frame_busca = QGroupBox('Buscar Deduções')
    layout = QGridLayout(frame_busca)

    # Material
    material_label = QLabel("Material:")
    layout.addWidget(material_label, 0, 0)
    g.DED_MATER_COMB = QComboBox()
    layout.addWidget(g.DED_MATER_COMB, 1, 0)
    g.DED_MATER_COMB.currentTextChanged.connect(lambda: buscar('dedução'))

    # Espessura
    espessura_label = QLabel("Espessura:")
    layout.addWidget(espessura_label, 0, 1)
    g.DED_ESPES_COMB = QComboBox()
    layout.addWidget(g.DED_ESPES_COMB, 1, 1)
    g.DED_ESPES_COMB.currentTextChanged.connect(lambda: buscar('dedução'))

    # Canal
    canal_label = QLabel("Canal:")
    layout.addWidget(canal_label, 0, 2)
    g.DED_CANAL_COMB = QComboBox()
    layout.addWidget(g.DED_CANAL_COMB, 1, 2)
    g.DED_CANAL_COMB.currentTextChanged.connect(lambda: buscar('dedução'))

    # Botão Limpar
    limpar_btn = QPushButton("Limpar")
    limpar_btn.setStyleSheet("background-color: lightyellow;")
    limpar_btn.clicked.connect(lambda: limpar_busca('dedução'))
    layout.addWidget(limpar_btn, 1, 3)

    return frame_busca


def criar_lista_deducoes(main_frame):
    """
    Cria a lista de deduções.
    """
    columns = ("Id", "Material", "Espessura", "Canal", "Dedução", "Observação", "Força")
    g.LIST_DED = QTreeWidget()
    g.LIST_DED.setHeaderLabels(["Material", "Espessura", "Canal", "Dedução", "Observação", "Força"])
    g.LIST_DED.setRootIsDecorated(False)
    
    # Configurar larguras das colunas
    g.LIST_DED.setColumnWidth(0, 80)   # Material
    g.LIST_DED.setColumnWidth(1, 60)   # Espessura
    g.LIST_DED.setColumnWidth(2, 60)   # Canal
    g.LIST_DED.setColumnWidth(3, 60)   # Dedução
    g.LIST_DED.setColumnWidth(4, 120)  # Observação
    g.LIST_DED.setColumnWidth(5, 60)   # Força

    listar('dedução')
    return g.LIST_DED


def criar_frame_edicoes(main_frame):
    """
    Cria o frame de edições.
    """
    frame_edicoes = QGroupBox('Nova Dedução' if not g.EDIT_DED else 'Editar Dedução')
    layout = QGridLayout(frame_edicoes)

    # Valor
    valor_label = QLabel("Valor:")
    layout.addWidget(valor_label, 0, 0)
    g.DED_VALOR_ENTRY = QLineEdit()
    layout.addWidget(g.DED_VALOR_ENTRY, 1, 0)

    # Observação
    observacao_label = QLabel("Observação:")
    layout.addWidget(observacao_label, 0, 1)
    g.DED_OBSER_ENTRY = QLineEdit()
    layout.addWidget(g.DED_OBSER_ENTRY, 1, 1)

    # Força
    forca_label = QLabel("Força:")
    layout.addWidget(forca_label, 0, 2)
    g.DED_FORCA_ENTRY = QLineEdit()
    layout.addWidget(g.DED_FORCA_ENTRY, 1, 2)

    return frame_edicoes


def configurar_botoes(main_frame, frame_edicoes):
    """
    Configura os botões de ação (Adicionar, Atualizar, Excluir).
    """
    layout = frame_edicoes.layout()
    
    if g.EDIT_DED:
        if g.DEDUC_FORM:
            g.DEDUC_FORM.setWindowTitle("Editar/Excluir Dedução")
        if g.LIST_DED:
            g.LIST_DED.itemSelectionChanged.connect(lambda: preencher_campos('dedução'))
        frame_edicoes.setTitle('Editar Dedução')

        # Botão Atualizar
        atualizar_btn = QPushButton("Atualizar")
        atualizar_btn.setStyleSheet("background-color: lightgreen;")
        atualizar_btn.clicked.connect(lambda: editar('dedução'))
        layout.addWidget(atualizar_btn, 1, 3)

        # Botão Excluir
        main_layout = main_frame.layout()
        excluir_btn = QPushButton("Excluir")
        excluir_btn.setStyleSheet("background-color: lightcoral;")
        excluir_btn.clicked.connect(lambda: excluir('dedução'))
        # Adicionar o botão em uma nova linha do layout principal
        main_layout.addWidget(excluir_btn, main_layout.rowCount(), 0)
    else:
        if g.DEDUC_FORM:
            g.DEDUC_FORM.setWindowTitle("Adicionar Dedução")
        frame_edicoes.setTitle('Nova Dedução')

        # Botão Adicionar
        adicionar_btn = QPushButton("Adicionar")
        adicionar_btn.setStyleSheet("background-color: lightblue;")
        adicionar_btn.clicked.connect(lambda: adicionar('dedução'))
        layout.addWidget(adicionar_btn, 1, 3)


def atualizar_comboboxes():
    """
    Atualiza os widgets de combobox.
    """
    tipos = ['material', 'espessura', 'canal']
    for tipo in tipos:
        atualizar_widgets(tipo)


def main(root):
    """
    Inicializa e exibe o formulário de gerenciamento de deduções.
    """
    configurar_janela(root)
    main_frame = configurar_main_frame(g.DEDUC_FORM)
    
    # Adicionar componentes ao layout principal
    layout = main_frame.layout()
    
    frame_busca = criar_frame_busca(main_frame)
    layout.addWidget(frame_busca, 0, 0)
    
    lista_deducoes = criar_lista_deducoes(main_frame)
    layout.addWidget(lista_deducoes, 1, 0)
    
    frame_edicoes = criar_frame_edicoes(main_frame)
    layout.addWidget(frame_edicoes, 2, 0)
    
    configurar_botoes(main_frame, frame_edicoes)
    atualizar_comboboxes()
    
    g.DEDUC_FORM.show()


if __name__ == "__main__":
    main(None)
