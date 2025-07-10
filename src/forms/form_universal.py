"""
Formulário Universal para todos os tipos de CRUD do sistema.

Este módulo unifica todos os formulários de adição/edição, eliminando duplicação de código
e facilitando manutenção através de configurações centralizadas.
"""

from PySide6.QtWidgets import (QDialog, QGridLayout, QGroupBox, QLabel,
                               QPushButton, QTreeWidget, QLineEdit, QComboBox,
                               QHBoxLayout, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.utils.janelas import posicionar_janela, aplicar_no_topo
from src.utils.interface import listar, limpar_busca, configurar_main_frame, atualizar_widgets
from src.utils.utilitarios import obter_caminho_icone
from src.utils.operacoes_crud import buscar, preencher_campos, excluir, editar, adicionar
from src.config import globals as g


# Configurações para cada tipo de formulário
FORM_CONFIGS = {
    'deducao': {
        'titulo': 'Formulário de Deduções',
        'size': (500, 460),
        'global_form': 'DEDUC_FORM',
        'global_edit': 'EDIT_DED',
        'busca': {
            'titulo': 'Buscar Deduções',
            'campos': [
                {'label': 'Material:', 'widget': 'combobox',
                 'global': 'DED_MATER_COMB', 'connect': 'buscar'},
                {'label': 'Espessura:', 'widget': 'combobox',
                 'global': 'DED_ESPES_COMB', 'connect': 'buscar'},
                {'label': 'Canal:', 'widget': 'combobox',
                 'global': 'DED_CANAL_COMB', 'connect': 'buscar'}
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
                {'label': 'Valor:', 'widget': 'entry',
                 'global': 'DED_VALOR_ENTRY', 'pos': (0, 0)},
                {'label': 'Observação:', 'widget': 'entry',
                 'global': 'DED_OBSER_ENTRY', 'pos': (0, 1)},
                {'label': 'Força:', 'widget': 'entry',
                 'global': 'DED_FORCA_ENTRY', 'pos': (0, 2)}
            ],
            'button_pos': (1, 3)
        },
        'post_init': lambda: atualizar_comboboxes(['material', 'espessura', 'canal']),
        'tipo_busca': 'dedução'
    },
    'material': {
        'titulo': 'Formulário de Materiais',
        'size': (340, 460),
        'global_form': 'MATER_FORM',
        'global_edit': 'EDIT_MAT',
        'busca': {
            'titulo': 'Buscar Materiais',
            'campos': [
                {'label': 'Nome:', 'widget': 'entry',
                 'global': 'MAT_BUSCA_ENTRY', 'connect': 'buscar'}
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
                {'label': 'Nome:', 'widget': 'entry',
                 'global': 'MAT_NOME_ENTRY', 'pos': (0, 0)},
                {'label': 'Densidade:', 'widget': 'entry',
                 'global': 'MAT_DENS_ENTRY', 'pos': (0, 1)},
                {'label': 'Escoamento:', 'widget': 'entry',
                 'global': 'MAT_ESCO_ENTRY', 'pos': (2, 0)},
                {'label': 'Elasticidade:', 'widget': 'entry',
                 'global': 'MAT_ELAS_ENTRY', 'pos': (2, 1)}
            ],
            'button_pos': (1, 2)
        },
        'tipo_busca': 'material'
    },
    'canal': {
        'titulo': 'Formulário de Canais',
        'size': (340, 460),
        'global_form': 'CANAL_FORM',
        'global_edit': 'EDIT_CANAL',
        'busca': {
            'titulo': 'Buscar Canais',
            'campos': [
                {'label': 'Valor:', 'widget': 'entry',
                 'global': 'CANAL_BUSCA_ENTRY', 'connect': 'buscar'}
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
                {'label': 'Valor:', 'widget': 'entry',
                 'global': 'CANAL_VALOR_ENTRY', 'pos': (0, 0)},
                {'label': 'Largura:', 'widget': 'entry',
                 'global': 'CANAL_LARGU_ENTRY', 'pos': (0, 1)},
                {'label': 'Altura:', 'widget': 'entry',
                 'global': 'CANAL_ALTUR_ENTRY', 'pos': (2, 0)},
                {'label': 'Comprimento total:', 'widget': 'entry',
                 'global': 'CANAL_COMPR_ENTRY', 'pos': (2, 1)},
                {'label': 'Observação:', 'widget': 'entry',
                 'global': 'CANAL_OBSER_ENTRY', 'pos': (4, 0), 'colspan': 2}
            ],
            'button_pos': (1, 2),
            'button_rowspan': 5
        },
        'tipo_busca': 'canal'
    },
    'espessura': {
        'titulo': 'Formulário de Espessuras',
        'size': (240, 320),
        'global_form': 'ESPES_FORM',
        'global_edit': 'EDIT_ESP',
        'busca': {
            'titulo': 'Buscar Espessuras',
            'campos': [
                {'label': 'Valor:', 'widget': 'entry',
                 'global': 'ESP_BUSCA_ENTRY', 'connect': 'buscar'}
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
                {'label': 'Valor:', 'widget': 'entry',
                 'global': 'ESP_VALOR_ENTRY', 'pos': (0, 0)}
            ],
            'button_pos': (0, 2),
            'inline_button': True  # Botão inline para espessuras
        },
        'tipo_busca': 'espessura'
    }
}


class ButtonConfigManager:
    """Gerencia a configuração de botões para os formulários."""

    def __init__(self, config, tipo):
        self.config = config
        self.tipo = tipo
        self.is_edit = getattr(g, config['global_edit'], False)
        self.tipo_operacao = config.get('tipo_busca', tipo)

    def get_button_layout_info(self, frame_edicoes):
        """Calcula informações de layout para os botões."""
        if not frame_edicoes or not frame_edicoes.layout():
            return None

        # Descobrir a última linha ocupada pelos campos
        linhas_ocupadas = [campo['pos'][0] +
                           1 for campo in self.config['edicao']['campos']]
        ultima_linha = max(linhas_ocupadas) + 1
        button_rowspan = self.config['edicao'].get('button_rowspan', 1)

        return {
            'ultima_linha': ultima_linha,
            'button_rowspan': button_rowspan,
            'layout': frame_edicoes.layout()
        }

    def create_update_button(self):
        """Cria o botão de atualizar."""
        atualizar_btn = QPushButton("✏️ Atualizar")
        atualizar_btn.setStyleSheet(self._get_green_button_style())
        atualizar_btn.clicked.connect(lambda: editar(self.tipo_operacao))
        return atualizar_btn

    def create_add_button(self):
        """Cria o botão de adicionar."""
        adicionar_btn = QPushButton("➕ Adicionar")
        adicionar_btn.setStyleSheet(self._get_blue_button_style())
        adicionar_btn.clicked.connect(lambda: adicionar(self.tipo_operacao))
        return adicionar_btn

    def update_form_titles(self, form_widget, frame_edicoes):
        """Atualiza os títulos do formulário e frame."""
        if not form_widget:
            return

        if self.is_edit:
            form_widget.setWindowTitle(
                f"Editar/Excluir {self.config['titulo'].split(' ')[-1]}")
        else:
            if self.tipo == 'espessura':
                form_widget.setWindowTitle("Adicionar Espessura")
            else:
                nome = self.config['titulo'].split(' ')[-1]
                form_widget.setWindowTitle(f"Novo {nome}")

        if frame_edicoes:
            if self.is_edit:
                frame_edicoes.setTitle(self.config['edicao']['titulo_edit'])
            else:
                frame_edicoes.setTitle(self.config['edicao']['titulo_novo'])

    def setup_list_connection(self):
        """Configura conexão de seleção da lista no modo edição."""
        if self.is_edit:
            list_widget = getattr(g, self.config['lista']['global'])
            if list_widget:
                list_widget.itemSelectionChanged.connect(
                    lambda: preencher_campos(self.tipo_operacao))

    def _get_green_button_style(self):
        """Retorna estilo CSS para botões verdes."""
        return """
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 4px 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """

    def _get_blue_button_style(self):
        """Retorna estilo CSS para botões azuis."""
        return """
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 4px 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """


class FormManager:
    """Gerencia a criação e configuração de formulários."""

    def __init__(self, tipo, config, root):
        self.tipo = tipo
        self.config = config
        self.root = root

    def setup_window(self):
        """Configura a janela principal do formulário."""
        form_attr = self.config['global_form']
        current_form = getattr(g, form_attr, None)

        if current_form:
            current_form.close()

        new_form = self._create_dialog()
        setattr(g, form_attr, new_form)
        return new_form

    def _create_dialog(self):
        """Cria o diálogo do formulário."""
        new_form = QDialog(self.root)
        new_form.setWindowTitle(self.config['titulo'])
        new_form.resize(*self.config['size'])
        new_form.setFixedSize(*self.config['size'])

        icone_path = obter_caminho_icone()
        new_form.setWindowIcon(QIcon(icone_path))

        aplicar_no_topo(new_form)
        posicionar_janela(new_form, None)

        return new_form

    def setup_main_layout(self, form):
        """Configura o layout principal do formulário."""
        main_frame = configurar_main_frame(form)
        return main_frame.layout()

    def create_search_frame(self):
        """Cria o frame de busca."""
        return criar_frame_busca(self.config, self.tipo)

    def create_list_widget(self):
        """Cria o widget de lista."""
        return criar_lista(self.config, self.tipo)

    def create_delete_button(self):
        """Cria o botão de excluir se necessário."""
        is_edit = getattr(g, self.config['global_edit'], False)
        if not is_edit:
            return None

        excluir_container = QWidget()
        excluir_layout = QHBoxLayout(excluir_container)
        excluir_layout.setContentsMargins(5, 5, 5, 5)

        excluir_btn = QPushButton("🗑️ Excluir")
        excluir_btn.setStyleSheet(self._get_red_button_style())
        excluir_btn.setFixedHeight(25)
        excluir_btn.setMinimumWidth(20)

        tipo_operacao = self.config.get('tipo_busca', self.tipo)
        excluir_btn.clicked.connect(lambda: excluir(tipo_operacao))

        excluir_layout.addWidget(excluir_btn)
        return excluir_container

    def create_edit_frame(self):
        """Cria o frame de edições se necessário."""
        is_edit = getattr(g, self.config['global_edit'], False)
        if not is_edit or self.tipo != 'espessura':
            return criar_frame_edicoes(self.config)
        return None

    def _get_red_button_style(self):
        """Retorna estilo CSS para botões vermelhos."""
        return """
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                padding: 4px 8px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
            QPushButton:pressed {
                background-color: #e53935;
            }
        """


def criar_label(layout, texto, pos):
    """
    Cria um rótulo (QLabel) no layout especificado.
    """
    linha, coluna = pos
    label = QLabel(texto)
    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    layout.addWidget(label, linha, coluna)
    return label


def criar_widget(layout, tipo, nome_global, pos, **kwargs):
    """
    Cria e configura um widget, o adiciona ao layout e o armazena em g.
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
    """
    frame_busca = QGroupBox(config['busca']['titulo'])
    layout = QGridLayout(frame_busca)
    tipo_busca = config.get('tipo_busca', tipo)

    # Criar campos
    for col, campo in enumerate(config['busca']['campos']):
        _criar_campo_busca(layout, campo, col, tipo_busca)

    # Botão Limpar
    _criar_botao_limpar_busca(layout, len(
        config['busca']['campos']), tipo_busca)

    return frame_busca


def _criar_campo_busca(layout, campo, col, tipo_busca):
    """Cria um campo individual de busca."""
    # Criar label
    criar_label(layout, campo['label'], (0, col))

    # Criar widget
    widget = criar_widget(layout, campo['widget'], campo['global'], (1, col))

    # Configurar conexões
    configurar_conexoes_busca(widget, campo, tipo_busca)


def _criar_botao_limpar_busca(layout, col, tipo_busca):
    """Cria o botão de limpar busca."""
    limpar_btn = QPushButton("🧹 Limpar")
    limpar_btn.setStyleSheet(obter_estilo_botao_amarelo())
    limpar_btn.clicked.connect(lambda: limpar_busca(tipo_busca))
    layout.addWidget(limpar_btn, 1, col)


def configurar_conexoes_busca(widget, campo_config, tipo_busca):
    """Configura conexões de busca para widgets."""
    if campo_config.get('connect') != 'buscar':
        return

    if campo_config['widget'] == 'entry':
        widget.textChanged.connect(lambda _, tb=tipo_busca: buscar(tb))
    elif campo_config['widget'] == 'combobox':
        widget.currentTextChanged.connect(lambda _, tb=tipo_busca: buscar(tb))


def criar_lista(config, tipo):
    """
    Cria a lista/árvore baseada na configuração.
    """
    tree_widget = QTreeWidget()
    tree_widget.setHeaderLabels(config['lista']['headers'])
    tree_widget.header().setDefaultAlignment(Qt.AlignCenter)
    tree_widget.setRootIsDecorated(False)

    # Configurar larguras das colunas
    for i, width in enumerate(config['lista']['widths']):
        tree_widget.setColumnWidth(i, width)

    setattr(g, config['lista']['global'], tree_widget)

    tipo_lista = config.get('tipo_busca', tipo)
    listar(tipo_lista)

    return tree_widget


def criar_frame_edicoes(config):
    """
    Cria o frame de edições baseado na configuração.
    """
    is_edit = getattr(g, config['global_edit'], False)
    titulo = config['edicao']['titulo_edit'] if is_edit else config['edicao']['titulo_novo']
    frame_edicoes = QGroupBox(titulo)
    layout = QGridLayout(frame_edicoes)

    # Criar campos
    for campo in config['edicao']['campos']:
        _criar_campo_edicao(layout, campo)

    return frame_edicoes


def _criar_campo_edicao(layout, campo):
    """Cria um campo individual de edição."""
    pos_label = campo['pos']
    pos_widget = (pos_label[0] + 1, pos_label[1])

    # Label
    criar_label(layout, campo['label'], pos_label)

    # Widget
    colspan = campo.get('colspan', 1)
    criar_widget(layout, campo['widget'],
                 campo['global'], pos_widget, colspan=colspan)


def configurar_botoes(config, frame_edicoes, tipo):
    """
    Configura os botões baseado na configuração.
    """
    button_manager = ButtonConfigManager(config, tipo)
    layout_info = button_manager.get_button_layout_info(frame_edicoes)

    if not layout_info:
        return

    _add_button_to_layout(button_manager, layout_info)
    _update_form_elements(button_manager, frame_edicoes)
    button_manager.setup_list_connection()


def _add_button_to_layout(button_manager, layout_info):
    """Adiciona o botão apropriado ao layout."""
    if button_manager.is_edit:
        button = button_manager.create_update_button()
    else:
        button = button_manager.create_add_button()

    layout_info['layout'].addWidget(
        button,
        layout_info['ultima_linha'],
        0,
        layout_info['button_rowspan'],
        layout_info['layout'].columnCount()
    )


def _update_form_elements(button_manager, frame_edicoes):
    """Atualiza elementos do formulário."""
    form_widget = getattr(g, button_manager.config['global_form'])
    button_manager.update_form_titles(form_widget, frame_edicoes)


def atualizar_comboboxes(tipos):
    """
    Atualiza comboboxes específicas.
    """
    for tipo in tipos:
        atualizar_widgets(tipo)


def obter_estilo_botao_amarelo():
    """Retorna estilo CSS para botões amarelos."""
    return """
        QPushButton {
            background-color: #ffd93d;
            color: #333;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ffcc02;
        }
        QPushButton:pressed {
            background-color: #e6b800;
        }
    """


def main(tipo, root):
    """
    Função principal universal para todos os formulários.
    """
    if tipo not in FORM_CONFIGS:
        raise ValueError(f"Tipo '{tipo}' não suportado")

    config = FORM_CONFIGS[tipo]
    form_manager = FormManager(tipo, config, root)

    # Configurar janela
    new_form = form_manager.setup_window()
    main_layout = form_manager.setup_main_layout(new_form)

    # Criar e adicionar componentes
    _setup_form_components(form_manager, main_layout)

    # Executar pós-inicialização
    _execute_post_init(config, tipo)

    new_form.show()


def _setup_form_components(form_manager, main_layout):
    """Configura os componentes do formulário."""
    # Frame de busca
    frame_busca = form_manager.create_search_frame()
    main_layout.addWidget(frame_busca, 0, 0)

    # Lista
    lista_widget = form_manager.create_list_widget()
    main_layout.addWidget(lista_widget, 1, 0)

    # Botão Excluir (se necessário)
    excluir_container = form_manager.create_delete_button()
    if excluir_container:
        main_layout.addWidget(excluir_container, 2, 0)

    # Frame de edições (se necessário)
    frame_edicoes = form_manager.create_edit_frame()
    if frame_edicoes:
        row_frame_edicoes = 3 if excluir_container else 2
        main_layout.addWidget(frame_edicoes, row_frame_edicoes, 0)

        # Configurar botões
        configurar_botoes(form_manager.config,
                          frame_edicoes, form_manager.tipo)


def _execute_post_init(config, tipo):
    """Executa pós-inicialização se necessário."""
    if 'post_init' in config:
        config['post_init']()

    # Garantir que a lista seja carregada
    tipo_lista = config.get('tipo_busca', tipo)
    listar(tipo_lista)


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
