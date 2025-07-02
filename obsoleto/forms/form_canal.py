"""
# Formulário de Canal
# Este módulo implementa o formulário de canal, permitindo a adição, edição
# e exclusão de canais. Ele utiliza a biblioteca PySide6 para a interface
# gráfica, o módulo globals para variáveis globais e o módulo funcoes para
# operações relacionadas ao banco de dados.
"""
try:
    from PySide6.QtWidgets import (QDialog, QGridLayout, 
                                   QGroupBox, QLabel, QPushButton, 
                                   QTreeWidget, QLineEdit)
    from PySide6.QtGui import QIcon
except ImportError:
    # Fallback para PyQt6 se PySide6 não estiver disponível
    from PyQt6.QtWidgets import (QDialog, QGridLayout, 
                                 QGroupBox, QLabel, QPushButton, 
                                 QTreeWidget, QLineEdit)
    from PyQt6.QtGui import QIcon

from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.interface import (listar,
                                 limpar_busca,
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
    Configura a janela principal do formulário.
    """
    if g.CANAL_FORM:
        g.CANAL_FORM.close()

    g.CANAL_FORM = QDialog(root)
    g.CANAL_FORM.setWindowTitle("Formulário de Canais")
    g.CANAL_FORM.resize(340, 420)
    g.CANAL_FORM.setFixedSize(340, 420)

    icone_path = obter_caminho_icone()
    g.CANAL_FORM.setWindowIcon(QIcon(icone_path))

    no_topo(g.CANAL_FORM)
    posicionar_janela(g.CANAL_FORM, None)


def criar_frame_busca(main_frame):
    """
    Cria o frame de busca.
    """
    frame_busca = QGroupBox('Buscar Canais')
    layout = QGridLayout(frame_busca)

    # Valor
    valor_label = QLabel("Valor:")
    layout.addWidget(valor_label, 0, 0)
    g.CANAL_BUSCA_ENTRY = QLineEdit()
    layout.addWidget(g.CANAL_BUSCA_ENTRY, 0, 1)
    g.CANAL_BUSCA_ENTRY.textChanged.connect(lambda: buscar('canal'))

    # Botão Limpar
    limpar_btn = QPushButton("Limpar")
    limpar_btn.setStyleSheet("background-color: lightyellow;")
    limpar_btn.clicked.connect(lambda: limpar_busca('canal'))
    layout.addWidget(limpar_btn, 0, 2)

    return frame_busca


def criar_lista_canais(main_frame):
    """
    Cria a lista de canais.
    """
    g.LIST_CANAL = QTreeWidget()
    g.LIST_CANAL.setHeaderLabels(["Canal", "Largura", "Altura", "Compr.", "Obs."])
    g.LIST_CANAL.setRootIsDecorated(False)
    
    # Configurar larguras das colunas
    g.LIST_CANAL.setColumnWidth(0, 60)   # Canal
    g.LIST_CANAL.setColumnWidth(1, 60)   # Largura
    g.LIST_CANAL.setColumnWidth(2, 60)   # Altura
    g.LIST_CANAL.setColumnWidth(3, 60)   # Compr.
    g.LIST_CANAL.setColumnWidth(4, 100)  # Obs.

    listar('canal')
    return g.LIST_CANAL


def criar_frame_edicoes(main_frame):
    """
    Cria o frame de edições.
    """
    frame_edicoes = QGroupBox('Novo Canal' if not g.EDIT_CANAL else 'Editar Canal')
    layout = QGridLayout(frame_edicoes)

    # Valor
    valor_label = QLabel("Valor:")
    layout.addWidget(valor_label, 0, 0)
    g.CANAL_VALOR_ENTRY = QLineEdit()
    layout.addWidget(g.CANAL_VALOR_ENTRY, 1, 0)

    # Largura
    largura_label = QLabel("Largura:")
    layout.addWidget(largura_label, 0, 1)
    g.CANAL_LARGU_ENTRY = QLineEdit()
    layout.addWidget(g.CANAL_LARGU_ENTRY, 1, 1)

    # Altura
    altura_label = QLabel("Altura:")
    layout.addWidget(altura_label, 2, 0)
    g.CANAL_ALTUR_ENTRY = QLineEdit()
    layout.addWidget(g.CANAL_ALTUR_ENTRY, 3, 0)

    # Comprimento total
    comprimento_label = QLabel("Comprimento total:")
    layout.addWidget(comprimento_label, 2, 1)
    g.CANAL_COMPR_ENTRY = QLineEdit()
    layout.addWidget(g.CANAL_COMPR_ENTRY, 3, 1)

    # Observação
    observacao_label = QLabel("Observação:")
    layout.addWidget(observacao_label, 4, 0)
    g.CANAL_OBSER_ENTRY = QLineEdit()
    layout.addWidget(g.CANAL_OBSER_ENTRY, 5, 0, 1, 2)  # colspan=2

    return frame_edicoes


def configurar_botoes(main_frame, frame_edicoes):
    """
    Configura os botões de ação (Adicionar, Atualizar, Excluir).
    """
    layout = frame_edicoes.layout()
    
    if g.EDIT_CANAL:
        if g.CANAL_FORM:
            g.CANAL_FORM.setWindowTitle("Editar/Excluir Canal")
        if g.LIST_CANAL:
            g.LIST_CANAL.itemSelectionChanged.connect(lambda: preencher_campos('canal'))
        frame_edicoes.setTitle('Editar Canal')

        # Botão Excluir
        main_layout = main_frame.layout()
        excluir_btn = QPushButton("Excluir")
        excluir_btn.setStyleSheet("background-color: lightcoral;")
        excluir_btn.clicked.connect(lambda: excluir('canal'))
        main_layout.addWidget(excluir_btn, main_layout.rowCount(), 0)

        # Botão Atualizar
        atualizar_btn = QPushButton("Atualizar")
        atualizar_btn.setStyleSheet("background-color: lightgreen;")
        atualizar_btn.clicked.connect(lambda: editar('canal'))
        layout.addWidget(atualizar_btn, 1, 2, 5, 1)  # rowspan=5
    else:
        if g.CANAL_FORM:
            g.CANAL_FORM.setWindowTitle("Novo Canal")
        frame_edicoes.setTitle('Novo Canal')
        
        # Botão Adicionar
        adicionar_btn = QPushButton("Adicionar")
        adicionar_btn.setStyleSheet("background-color: lightblue;")
        adicionar_btn.clicked.connect(lambda: adicionar('canal'))
        layout.addWidget(adicionar_btn, 1, 2, 5, 1)  # rowspan=5


def main(root):
    """
    Inicializa e exibe o formulário de gerenciamento de canais.
    """
    configurar_janela(root)
    main_frame = configurar_main_frame(g.CANAL_FORM)
    
    # Adicionar componentes ao layout principal
    layout = main_frame.layout()
    
    frame_busca = criar_frame_busca(main_frame)
    layout.addWidget(frame_busca, 0, 0)
    
    lista_canais = criar_lista_canais(main_frame)
    layout.addWidget(lista_canais, 1, 0)
    
    frame_edicoes = criar_frame_edicoes(main_frame)
    layout.addWidget(frame_edicoes, 2, 0)
    
    configurar_botoes(main_frame, frame_edicoes)
    
    g.CANAL_FORM.show()


if __name__ == "__main__":
    main(None)
