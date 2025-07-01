"""
# Formulário de Espessura
# Este módulo implementa a interface gráfica para gerenciar espessuras de materiais.
# Ele permite adicionar, editar e excluir registros de espessuras, utilizando a
# biblioteca PySide6 para a construção da interface. As variáveis globais são
# gerenciadas pelo módulo `globals`, enquanto as operações de banco de dados
# são realizadas pelo módulo `funcoes`.
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
                                      excluir,
                                      adicionar
                                      )
from src.config import globals as g


def configurar_janela(root):
    """
    Configura a janela principal do formulário de espessuras.
    """
    if g.ESPES_FORM:
        g.ESPES_FORM.close()

    g.ESPES_FORM = QDialog(root)
    g.ESPES_FORM.setWindowTitle("Formulário de Espessuras")
    g.ESPES_FORM.resize(240, 280)
    g.ESPES_FORM.setFixedSize(240, 280)

    icone_path = obter_caminho_icone()
    g.ESPES_FORM.setWindowIcon(QIcon(icone_path))

    no_topo(g.ESPES_FORM)
    posicionar_janela(g.ESPES_FORM, None)


def criar_frame_busca(main_frame):
    """
    Cria o frame de busca.
    """
    frame_busca = QGroupBox('Buscar Espessuras')
    layout = QGridLayout(frame_busca)

    # Valor
    valor_label = QLabel("Valor:")
    layout.addWidget(valor_label, 0, 0)
    g.ESP_BUSCA_ENTRY = QLineEdit()
    layout.addWidget(g.ESP_BUSCA_ENTRY, 0, 1)
    g.ESP_BUSCA_ENTRY.textChanged.connect(lambda: buscar('espessura'))

    # Botão Limpar
    limpar_btn = QPushButton("Limpar")
    limpar_btn.setStyleSheet("background-color: lightyellow;")
    limpar_btn.clicked.connect(lambda: limpar_busca('espessura'))
    layout.addWidget(limpar_btn, 0, 2)

    return frame_busca


def criar_lista_espessuras(main_frame):
    """
    Cria a lista de espessuras.
    """
    g.LIST_ESP = QTreeWidget()
    g.LIST_ESP.setHeaderLabels(["Valor"])
    g.LIST_ESP.setRootIsDecorated(False)
    
    # Configurar largura da coluna
    g.LIST_ESP.setColumnWidth(0, 180)  # Valor

    listar('espessura')
    return g.LIST_ESP


def criar_frame_edicoes(main_frame):
    """
    Cria o frame de edições.
    """
    frame_edicoes = QGroupBox('Adicionar Espessura' if not g.EDIT_ESP else 'Editar Espessura')
    layout = QGridLayout(frame_edicoes)

    # Valor
    valor_label = QLabel("Valor:")
    layout.addWidget(valor_label, 0, 0)
    g.ESP_VALOR_ENTRY = QLineEdit()
    layout.addWidget(g.ESP_VALOR_ENTRY, 0, 1)
    
    # Botão Adicionar
    adicionar_btn = QPushButton("Adicionar")
    adicionar_btn.setStyleSheet("background-color: lightblue;")
    adicionar_btn.clicked.connect(lambda: adicionar('espessura'))
    layout.addWidget(adicionar_btn, 0, 2)

    return frame_edicoes


def configurar_botoes(main_frame):
    """
    Configura os botões de ação (Excluir).
    """
    if g.ESPES_FORM is not None:
        if g.EDIT_ESP:
            g.ESPES_FORM.setWindowTitle("Editar/Excluir Espessura")
            
            # Botão Excluir
            main_layout = main_frame.layout()
            excluir_btn = QPushButton("Excluir")
            excluir_btn.setStyleSheet("background-color: lightcoral;")
            excluir_btn.clicked.connect(lambda: excluir('espessura'))
            main_layout.addWidget(excluir_btn, main_layout.rowCount(), 0)
        else:
            g.ESPES_FORM.setWindowTitle("Adicionar Espessura")
    else:
        print("Erro: g.ESPES_FORM não foi inicializado.")


def main(root):
    """
    Inicializa e exibe o formulário de gerenciamento de espessuras.
    """
    configurar_janela(root)
    main_frame = configurar_main_frame(g.ESPES_FORM)
    
    # Adicionar componentes ao layout principal
    layout = main_frame.layout()
    
    frame_busca = criar_frame_busca(main_frame)
    layout.addWidget(frame_busca, 0, 0)
    
    lista_espessuras = criar_lista_espessuras(main_frame)
    layout.addWidget(lista_espessuras, 1, 0)
    
    if not g.EDIT_ESP:
        frame_edicoes = criar_frame_edicoes(main_frame)
        layout.addWidget(frame_edicoes, 2, 0)
    
    configurar_botoes(main_frame)
    
    g.ESPES_FORM.show()


if __name__ == "__main__":
    main(None)
