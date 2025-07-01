"""
# Formulário de Material
# Este módulo contém a implementação do formulário de materiais, que permite
# adicionar, editar e excluir materiais. O formulário é
# construído usando a biblioteca PySide6 e utiliza o módulo globals para
# armazenar variáveis globais e o módulo funcoes para realizar operações
# relacionadas ao banco de dados.
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
    Configura a janela principal do formulário de materiais.
    """
    if g.MATER_FORM:
        g.MATER_FORM.close()

    g.MATER_FORM = QDialog(root)
    g.MATER_FORM.setWindowTitle("Formulário de Materiais")
    g.MATER_FORM.resize(340, 420)
    g.MATER_FORM.setFixedSize(340, 420)

    icone_path = obter_caminho_icone()
    g.MATER_FORM.setWindowIcon(QIcon(icone_path))

    no_topo(g.MATER_FORM)
    posicionar_janela(g.MATER_FORM, None)


def criar_frame_busca(main_frame):
    """
    Cria o frame de busca.
    """
    frame_busca = QGroupBox('Buscar Materiais')
    layout = QGridLayout(frame_busca)

    # Nome
    nome_label = QLabel("Nome:")
    layout.addWidget(nome_label, 0, 0)
    g.MAT_BUSCA_ENTRY = QLineEdit()
    layout.addWidget(g.MAT_BUSCA_ENTRY, 0, 1)
    g.MAT_BUSCA_ENTRY.textChanged.connect(lambda: buscar('material'))

    # Botão Limpar
    limpar_btn = QPushButton("Limpar")
    limpar_btn.setStyleSheet("background-color: lightyellow;")
    limpar_btn.clicked.connect(lambda: limpar_busca('material'))
    layout.addWidget(limpar_btn, 0, 2)

    return frame_busca


def criar_lista_materiais(main_frame):
    """
    Cria a lista de materiais.
    """
    g.LIST_MAT = QTreeWidget()
    g.LIST_MAT.setHeaderLabels(["Nome", "Densidade", "Escoamento", "Elasticidade"])
    g.LIST_MAT.setRootIsDecorated(False)
    
    # Configurar larguras das colunas
    g.LIST_MAT.setColumnWidth(0, 100)  # Nome
    g.LIST_MAT.setColumnWidth(1, 80)   # Densidade
    g.LIST_MAT.setColumnWidth(2, 80)   # Escoamento
    g.LIST_MAT.setColumnWidth(3, 80)   # Elasticidade

    listar('material')
    return g.LIST_MAT


def criar_frame_edicoes(main_frame):
    """
    Cria o frame de edições.
    """
    frame_edicoes = QGroupBox('Novo Material' if not g.EDIT_MAT else 'Editar Material')
    layout = QGridLayout(frame_edicoes)

    # Nome
    nome_label = QLabel("Nome:")
    layout.addWidget(nome_label, 0, 0)
    g.MAT_NOME_ENTRY = QLineEdit()
    layout.addWidget(g.MAT_NOME_ENTRY, 1, 0)

    # Densidade
    densidade_label = QLabel("Densidade:")
    layout.addWidget(densidade_label, 0, 1)
    g.MAT_DENS_ENTRY = QLineEdit()
    layout.addWidget(g.MAT_DENS_ENTRY, 1, 1)

    # Escoamento
    escoamento_label = QLabel("Escoamento:")
    layout.addWidget(escoamento_label, 2, 0)
    g.MAT_ESCO_ENTRY = QLineEdit()
    layout.addWidget(g.MAT_ESCO_ENTRY, 3, 0)

    # Elasticidade
    elasticidade_label = QLabel("Elasticidade:")
    layout.addWidget(elasticidade_label, 2, 1)
    g.MAT_ELAS_ENTRY = QLineEdit()
    layout.addWidget(g.MAT_ELAS_ENTRY, 3, 1)

    return frame_edicoes


def configurar_botoes(main_frame, frame_edicoes):
    """
    Configura os botões de ação (Adicionar, Atualizar, Excluir).
    """
    layout = frame_edicoes.layout()
    
    if g.MATER_FORM is not None:
        if g.EDIT_MAT:
            g.MATER_FORM.setWindowTitle("Editar/Excluir Material")
            if g.LIST_MAT is not None:
                g.LIST_MAT.itemSelectionChanged.connect(lambda: preencher_campos('material'))
            else:
                print("Erro: g.LIST_MAT não foi inicializado.")
            frame_edicoes.setTitle('Editar Material')

            # Botão Excluir
            main_layout = main_frame.layout()
            excluir_btn = QPushButton("Excluir")
            excluir_btn.setStyleSheet("background-color: lightcoral;")
            excluir_btn.clicked.connect(lambda: excluir('material'))
            main_layout.addWidget(excluir_btn, main_layout.rowCount(), 0)

            # Botão Atualizar
            atualizar_btn = QPushButton("Atualizar")
            atualizar_btn.setStyleSheet("background-color: lightgreen;")
            atualizar_btn.clicked.connect(lambda: editar('material'))
            layout.addWidget(atualizar_btn, 1, 2, 3, 1)  # rowspan=3
        else:
            g.MATER_FORM.setWindowTitle("Adicionar Material")
            frame_edicoes.setTitle('Novo Material')
            
            # Botão Adicionar
            adicionar_btn = QPushButton("Adicionar")
            adicionar_btn.setStyleSheet("background-color: lightblue;")
            adicionar_btn.clicked.connect(lambda: adicionar('material'))
            layout.addWidget(adicionar_btn, 1, 2, 3, 1)  # rowspan=3
    else:
        print("Erro: g.MATER_FORM não foi inicializado.")


def main(root):
    """
    Inicializa e exibe o formulário de gerenciamento de materiais.
    """
    configurar_janela(root)
    main_frame = configurar_main_frame(g.MATER_FORM)
    
    # Adicionar componentes ao layout principal
    layout = main_frame.layout()
    
    frame_busca = criar_frame_busca(main_frame)
    layout.addWidget(frame_busca, 0, 0)
    
    lista_materiais = criar_lista_materiais(main_frame)
    layout.addWidget(lista_materiais, 1, 0)
    
    frame_edicoes = criar_frame_edicoes(main_frame)
    layout.addWidget(frame_edicoes, 2, 0)
    
    configurar_botoes(main_frame, frame_edicoes)
    
    g.MATER_FORM.show()


if __name__ == "__main__":
    main(None)
