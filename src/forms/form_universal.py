"""
Formulário Universal para todos os tipos de CRUD do sistema.
Este módulo unifica todos os formulários de adição/edição, eliminando duplicação de código
e facilitando manutenção através de configurações centralizadas.
"""
try:
    from PySide6.QtWidgets import (QDialog, QGridLayout, QGroupBox, QLabel, 
                                   QPushButton, QTreeWidget, QLineEdit, QComboBox)
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
except ImportError:
    # Fallback para PyQt6 se PySide6 não estiver disponível
    from PyQt6.QtWidgets import (QDialog, QGridLayout, QGroupBox, QLabel, 
                                 QPushButton, QTreeWidget, QLineEdit, QComboBox)
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon

from src.utils.janelas import no_topo, posicionar_janela
from src.utils.interface import listar, limpar_busca, configurar_main_frame, atualizar_widgets
from src.utils.utilitarios import obter_caminho_icone
from src.utils.operacoes_crud import buscar, preencher_campos, excluir, editar, adicionar
from src.config import globals as g


# Configurações para cada tipo de formulário
FORM_CONFIGS = {
    'deducao': {
        'titulo': 'Formulário de Deduções',
        'size': (500, 420),
        'global_form': 'DEDUC_FORM',
        'global_edit': 'EDIT_DED',
        'busca': {
            'titulo': 'Buscar Deduções',
            'campos': [
                {'label': 'Material:', 'widget': 'combobox', 'global': 'DED_MATER_COMB', 'connect': 'buscar'},
                {'label': 'Espessura:', 'widget': 'combobox', 'global': 'DED_ESPES_COMB', 'connect': 'buscar'},
                {'label': 'Canal:', 'widget': 'combobox', 'global': 'DED_CANAL_COMB', 'connect': 'buscar'}
            ]
        },
        'lista': {
            'global': 'LIST_DED',
            'headers': ["Material", "Espessura", "Canal", "Dedução", "Observação", "Força"],
            'widths': [80, 60, 60, 60, 120, 60]
        },
        'edicao': {
            'titulo_novo': 'Nova Dedução',
            'titulo_edit': 'Editar Dedução',
            'campos': [
                {'label': 'Valor:', 'widget': 'entry', 'global': 'DED_VALOR_ENTRY', 'pos': (0, 0)},
                {'label': 'Observação:', 'widget': 'entry', 'global': 'DED_OBSER_ENTRY', 'pos': (0, 1)},
                {'label': 'Força:', 'widget': 'entry', 'global': 'DED_FORCA_ENTRY', 'pos': (0, 2)}
            ],
            'button_pos': (1, 3)
        },
        'post_init': lambda: atualizar_comboboxes(['material', 'espessura', 'canal']),
        'tipo_busca': 'dedução'
    },
    
    'material': {
        'titulo': 'Formulário de Materiais',
        'size': (340, 420),
        'global_form': 'MATER_FORM',
        'global_edit': 'EDIT_MAT',
        'busca': {
            'titulo': 'Buscar Materiais',
            'campos': [
                {'label': 'Nome:', 'widget': 'entry', 'global': 'MAT_BUSCA_ENTRY', 'connect': 'buscar'}
            ]
        },
        'lista': {
            'global': 'LIST_MAT',
            'headers': ["Nome", "Densidade", "Escoamento", "Elasticidade"],
            'widths': [100, 80, 80, 80]
        },
        'edicao': {
            'titulo_novo': 'Novo Material',
            'titulo_edit': 'Editar Material',
            'campos': [
                {'label': 'Nome:', 'widget': 'entry', 'global': 'MAT_NOME_ENTRY', 'pos': (0, 0)},
                {'label': 'Densidade:', 'widget': 'entry', 'global': 'MAT_DENS_ENTRY', 'pos': (0, 1)},
                {'label': 'Escoamento:', 'widget': 'entry', 'global': 'MAT_ESCO_ENTRY', 'pos': (2, 0)},
                {'label': 'Elasticidade:', 'widget': 'entry', 'global': 'MAT_ELAS_ENTRY', 'pos': (2, 1)}
            ],
            'button_pos': (1, 2)
        },
        'tipo_busca': 'material'
    },
    
    'canal': {
        'titulo': 'Formulário de Canais',
        'size': (340, 420),
        'global_form': 'CANAL_FORM',
        'global_edit': 'EDIT_CANAL',
        'busca': {
            'titulo': 'Buscar Canais',
            'campos': [
                {'label': 'Valor:', 'widget': 'entry', 'global': 'CANAL_BUSCA_ENTRY', 'connect': 'buscar'}
            ]
        },
        'lista': {
            'global': 'LIST_CANAL',
            'headers': ["Canal", "Largura", "Altura", "Compr.", "Obs."],
            'widths': [60, 60, 60, 60, 100]
        },
        'edicao': {
            'titulo_novo': 'Novo Canal',
            'titulo_edit': 'Editar Canal',
            'campos': [
                {'label': 'Valor:', 'widget': 'entry', 'global': 'CANAL_VALOR_ENTRY', 'pos': (0, 0)},
                {'label': 'Largura:', 'widget': 'entry', 'global': 'CANAL_LARGU_ENTRY', 'pos': (0, 1)},
                {'label': 'Altura:', 'widget': 'entry', 'global': 'CANAL_ALTUR_ENTRY', 'pos': (2, 0)},
                {'label': 'Comprimento total:', 'widget': 'entry', 'global': 'CANAL_COMPR_ENTRY', 'pos': (2, 1)},
                {'label': 'Observação:', 'widget': 'entry', 'global': 'CANAL_OBSER_ENTRY', 'pos': (4, 0), 'colspan': 2}
            ],
            'button_pos': (1, 2),
            'button_rowspan': 5
        },
        'tipo_busca': 'canal'
    },
    
    'espessura': {
        'titulo': 'Formulário de Espessuras',
        'size': (240, 280),
        'global_form': 'ESPES_FORM',
        'global_edit': 'EDIT_ESP',
        'busca': {
            'titulo': 'Buscar Espessuras',
            'campos': [
                {'label': 'Valor:', 'widget': 'entry', 'global': 'ESP_BUSCA_ENTRY', 'connect': 'buscar'}
            ]
        },
        'lista': {
            'global': 'LIST_ESP',
            'headers': ["Valor"],
            'widths': [180]
        },
        'edicao': {
            'titulo_novo': 'Adicionar Espessura',
            'titulo_edit': 'Editar Espessura',
            'campos': [
                {'label': 'Valor:', 'widget': 'entry', 'global': 'ESP_VALOR_ENTRY', 'pos': (0, 0)}
            ],
            'button_pos': (0, 2),
            'inline_button': True  # Botão inline para espessuras
        },
        'tipo_busca': 'espessura'
    }
}


def criar_label(layout, texto, pos, **kwargs):
    """
    Cria um rótulo (QLabel) no layout especificado.
    
    Args:
        layout (QGridLayout): Layout onde o rótulo será criado.
        texto (str): Texto do rótulo.
        pos (tuple): Tupla contendo a linha e a coluna onde o rótulo será posicionado.
        **kwargs: Argumentos adicionais para o widget QLabel.
    """
    linha, coluna = pos
    label = QLabel(texto)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    layout.addWidget(label, linha, coluna)
    return label


def criar_widget(layout, tipo, nome_global, pos, **kwargs):
    """
    Cria e configura um widget, o adiciona ao layout e o armazena em g.
    
    Args:
        layout (QGridLayout): Layout onde o widget será criado.
        tipo (str): Tipo do widget ('entry', 'combobox', 'label').
        nome_global (str): Nome da variável global onde o widget será armazenado.
        pos (tuple): Tupla contendo a linha e a coluna onde o widget será posicionado.
        **kwargs: Argumentos adicionais para o widget.
    """
    if tipo == 'entry':
        widget = QLineEdit()
        widget.setFixedHeight(20)
    elif tipo == 'combobox':
        widget = QComboBox()
        widget.setFixedHeight(20)
    else:
        return None
    
    colspan = kwargs.get('colspan', 1)
    rowspan = kwargs.get('rowspan', 1)
    linha, coluna = pos
    
    layout.addWidget(widget, linha, coluna, rowspan, colspan)
    setattr(g, nome_global, widget)
    return widget


def criar_frame_busca(config, tipo):
    """
    Cria o frame de busca baseado na configuração.
    
    Args:
        config (dict): Configuração do formulário.
        tipo (str): Tipo do formulário.
    """
    frame_busca = QGroupBox(config['busca']['titulo'])
    layout = QGridLayout(frame_busca)
    
    col = 0
    for campo in config['busca']['campos']:
        # Criar label
        criar_label(layout, campo['label'], (0, col))
        
        # Criar widget
        widget = criar_widget(layout, campo['widget'], campo['global'], (1, col))
        
        # Conectar eventos
        if campo.get('connect') == 'buscar':
            tipo_busca = config.get('tipo_busca', tipo)
            if campo['widget'] == 'entry':
                widget.textChanged.connect(lambda: buscar(tipo_busca))
            elif campo['widget'] == 'combobox':
                widget.currentTextChanged.connect(lambda: buscar(tipo_busca))
        
        col += 1
    
    # Botão Limpar
    limpar_btn = QPushButton("Limpar")
    limpar_btn.setStyleSheet("background-color: lightyellow;")
    tipo_busca = config.get('tipo_busca', tipo)
    limpar_btn.clicked.connect(lambda: limpar_busca(tipo_busca))
    layout.addWidget(limpar_btn, 1, col)
    
    return frame_busca


def criar_lista(config, tipo):
    """
    Cria a lista/árvore baseada na configuração.
    
    Args:
        config (dict): Configuração do formulário.
        tipo (str): Tipo do formulário.
    """
    tree_widget = QTreeWidget()
    tree_widget.setHeaderLabels(config['lista']['headers'])
    tree_widget.setRootIsDecorated(False)
    
    # Configurar larguras das colunas
    for i, width in enumerate(config['lista']['widths']):
        tree_widget.setColumnWidth(i, width)
    
    setattr(g, config['lista']['global'], tree_widget)
    tipo_lista = config.get('tipo_busca', tipo)
    listar(tipo_lista)
    return tree_widget


def criar_frame_edicoes(config, tipo):
    """
    Cria o frame de edições baseado na configuração.
    
    Args:
        config (dict): Configuração do formulário.
        tipo (str): Tipo do formulário.
    """
    is_edit = getattr(g, config['global_edit'], False)
    titulo = config['edicao']['titulo_edit'] if is_edit else config['edicao']['titulo_novo']
    
    frame_edicoes = QGroupBox(titulo)
    layout = QGridLayout(frame_edicoes)
    
    # Criar campos
    for campo in config['edicao']['campos']:
        pos_label = campo['pos']
        pos_widget = (pos_label[0] + 1, pos_label[1])
        
        # Label
        criar_label(layout, campo['label'], pos_label)
        
        # Widget
        colspan = campo.get('colspan', 1)
        criar_widget(layout, campo['widget'], campo['global'], pos_widget, colspan=colspan)
    
    return frame_edicoes


def configurar_botoes(config, main_frame, frame_edicoes, tipo):
    """
    Configura os botões baseado na configuração.
    
    Args:
        config (dict): Configuração do formulário.
        main_frame: Frame principal.
        frame_edicoes: Frame de edições.
        tipo (str): Tipo do formulário.
    """
    is_edit = getattr(g, config['global_edit'], False)
    layout = frame_edicoes.layout() if frame_edicoes else None
    tipo_operacao = config.get('tipo_busca', tipo)
    
    if is_edit:
        # Modo edição
        form_widget = getattr(g, config['global_form'])
        if form_widget:
            form_widget.setWindowTitle(f"Editar/Excluir {config['titulo'].split(' ')[-1]}")
        
        # Conectar seleção da lista
        list_widget = getattr(g, config['lista']['global'])
        if list_widget:
            list_widget.itemSelectionChanged.connect(lambda: preencher_campos(tipo_operacao))
        
        # Atualizar título do frame de edições
        if frame_edicoes:
            frame_edicoes.setTitle(config['edicao']['titulo_edit'])
        
        # Botão Excluir (no layout principal)
        main_layout = main_frame.layout()
        excluir_btn = QPushButton("Excluir")
        excluir_btn.setStyleSheet("background-color: lightcoral;")
        excluir_btn.clicked.connect(lambda: excluir(tipo_operacao))
        main_layout.addWidget(excluir_btn, main_layout.rowCount(), 0)
        
        # Botão Atualizar (no frame de edições, se existir)
        if layout:
            atualizar_btn = QPushButton("Atualizar")
            atualizar_btn.setStyleSheet("background-color: lightgreen;")
            atualizar_btn.clicked.connect(lambda: editar(tipo_operacao))
            
            button_pos = config['edicao']['button_pos']
            button_rowspan = config['edicao'].get('button_rowspan', 1)
            layout.addWidget(atualizar_btn, button_pos[0], button_pos[1], button_rowspan, 1)
    else:
        # Modo adição
        form_widget = getattr(g, config['global_form'])
        if form_widget:
            # Atualizar título baseado no tipo
            if tipo == 'espessura':
                form_widget.setWindowTitle("Adicionar Espessura")
            else:
                nome = config['titulo'].split(' ')[-1]
                form_widget.setWindowTitle(f"Novo {nome}")
        
        # Atualizar título do frame de edições
        if frame_edicoes:
            frame_edicoes.setTitle(config['edicao']['titulo_novo'])
        
        # Botão Adicionar (no frame de edições, se existir)
        if layout:
            adicionar_btn = QPushButton("Adicionar")
            adicionar_btn.setStyleSheet("background-color: lightblue;")
            adicionar_btn.clicked.connect(lambda: adicionar(tipo_operacao))
            
            button_pos = config['edicao']['button_pos']
            button_rowspan = config['edicao'].get('button_rowspan', 1)
            layout.addWidget(adicionar_btn, button_pos[0], button_pos[1], button_rowspan, 1)


def atualizar_comboboxes(tipos):
    """
    Atualiza comboboxes específicas.
    
    Args:
        tipos (list): Lista de tipos para atualizar.
    """
    for tipo in tipos:
        atualizar_widgets(tipo)


def main(tipo, root):
    """
    Função principal universal para todos os formulários.
    
    Args:
        tipo (str): Tipo do formulário ('deducao', 'material', 'canal', 'espessura').
        root: Widget pai.
    """
    if tipo not in FORM_CONFIGS:
        raise ValueError(f"Tipo '{tipo}' não suportado")
    
    config = FORM_CONFIGS[tipo]
    
    # Configurar janela
    form_attr = config['global_form']
    current_form = getattr(g, form_attr, None)
    if current_form:
        current_form.close()
    
    new_form = QDialog(root)
    new_form.setWindowTitle(config['titulo'])
    new_form.resize(*config['size'])
    new_form.setFixedSize(*config['size'])
    
    icone_path = obter_caminho_icone()
    new_form.setWindowIcon(QIcon(icone_path))
    
    no_topo(new_form)
    posicionar_janela(new_form, None)
    
    setattr(g, form_attr, new_form)
    
    # Criar componentes
    main_frame = configurar_main_frame(new_form)
    layout = main_frame.layout()
    
    # Frame de busca
    frame_busca = criar_frame_busca(config, tipo)
    layout.addWidget(frame_busca, 0, 0)
    
    # Lista
    lista_widget = criar_lista(config, tipo)
    layout.addWidget(lista_widget, 1, 0)
    
    # Frame de edições (só para não-edição em espessuras ou sempre para outros)
    is_edit = getattr(g, config['global_edit'], False)
    frame_edicoes = None
    
    if not is_edit or tipo != 'espessura':
        frame_edicoes = criar_frame_edicoes(config, tipo)
        layout.addWidget(frame_edicoes, 2, 0)
    
    # Configurar botões
    configurar_botoes(config, main_frame, frame_edicoes, tipo)
    
    # Executar pós-inicialização se necessário
    if 'post_init' in config:
        config['post_init']()
    
    new_form.show()


# Funções de compatibilidade para manter a API existente
def form_deducao_main(root):
    """Wrapper para manter compatibilidade com form_deducao."""
    main('deducao', root)


def form_material_main(root):
    """Wrapper para manter compatibilidade com form_material."""
    main('material', root)


def form_canal_main(root):
    """Wrapper para manter compatibilidade com form_canal."""
    main('canal', root)


def form_espessura_main(root):
    """Wrapper para manter compatibilidade com form_espessura."""
    main('espessura', root)


if __name__ == "__main__":
    # Teste básico
    main('material', None)
