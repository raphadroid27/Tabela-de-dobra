"""
Formulário Universal para todos os tipos de CRUD do sistema.

Este módulo unifica todos os formulários de adição/edição, eliminando duplicação de código
e facilitando manutenção através de configurações centralizadas.

Versão atualizada com botões de ação fora do grid para melhor organização visual.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import Shiboken

from src.config import globals as g
from src.forms.common.ui_helpers import configure_frameless_dialog
from src.utils.controlador import (
    adicionar,
    buscar_debounced,
    editar,
    excluir,
    preencher_campos,
)
from src.utils.estilo import (
    aplicar_estilo_botao,
    aplicar_estilo_table_widget,
)
from src.utils.interface import (
    FormWidgetUpdater,
    limpar_busca,
    listar,
)
from src.utils.janelas import Janela
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco

# Configurações para cada tipo de formulário
FORM_CONFIGS = {
    "deducao": {
        "titulo": "Formulário de Deduções",
        "size": (500, 500),
        "global_form": "DEDUC_FORM",
        "global_edit": "EDIT_DED",
        "busca": {
            "titulo": "Buscar Deduções",
            "campos": [
                {
                    "label": "Material:",
                    "widget": "combobox",
                    "global": "DED_MATER_COMB",
                    "connect": "buscar",
                },
                {
                    "label": "Espessura:",
                    "widget": "combobox",
                    "global": "DED_ESPES_COMB",
                    "connect": "buscar",
                },
                {
                    "label": "Canal:",
                    "widget": "combobox",
                    "global": "DED_CANAL_COMB",
                    "connect": "buscar",
                },
            ],
        },
        "lista": {
            "global": "LIST_DED",
            "headers": [
                "Material",
                "Espessura",
                "Canal",
                "Dedução",
                "Observação",
                "Força (t/m)",
            ],
            "widths": [80, 60, 60, 60, 120, 60],
        },
        "edicao": {
            "titulo_novo": "Nova Dedução",
            "titulo_edit": "Editar Dedução",
            "campos": [
                {
                    "label": "Valor:",
                    "widget": "entry",
                    "global": "DED_VALOR_ENTRY",
                    "pos": (0, 0),
                },
                {
                    "label": "Observação:",
                    "widget": "entry",
                    "global": "DED_OBSER_ENTRY",
                    "pos": (0, 1),
                },
                {
                    "label": "Força (t/m):",
                    "widget": "entry",
                    "global": "DED_FORCA_ENTRY",
                    "pos": (0, 2),
                },
            ],
        },
        "post_init": lambda: FormWidgetUpdater().atualizar(
            ["material", "espessura", "canal"]
        ),
        "tipo_busca": "dedução",
    },
    "material": {
        "titulo": "Formulário de Materiais",
        "size": (360, 500),
        "global_form": "MATER_FORM",
        "global_edit": "EDIT_MAT",
        "busca": {
            "titulo": "Buscar Materiais",
            "campos": [
                {
                    "label": "Nome:",
                    "widget": "entry",
                    "global": "MAT_BUSCA_ENTRY",
                    "connect": "buscar",
                }
            ],
        },
        "lista": {
            "global": "LIST_MAT",
            "headers": ["Nome", "Densidade", "Escoamento", "Elasticidade"],
            "widths": [100, 80, 80, 80],
        },
        "edicao": {
            "titulo_novo": "Novo Material",
            "titulo_edit": "Editar Material",
            "campos": [
                {
                    "label": "Nome:",
                    "widget": "entry",
                    "global": "MAT_NOME_ENTRY",
                    "pos": (0, 0),
                },
                {
                    "label": "Densidade:",
                    "widget": "entry",
                    "global": "MAT_DENS_ENTRY",
                    "pos": (0, 1),
                },
                {
                    "label": "Escoamento:",
                    "widget": "entry",
                    "global": "MAT_ESCO_ENTRY",
                    "pos": (2, 0),
                },
                {
                    "label": "Elasticidade:",
                    "widget": "entry",
                    "global": "MAT_ELAS_ENTRY",
                    "pos": (2, 1),
                },
            ],
        },
        "tipo_busca": "material",
    },
    "canal": {
        "titulo": "Formulário de Canais",
        "size": (360, 500),
        "global_form": "CANAL_FORM",
        "global_edit": "EDIT_CANAL",
        "busca": {
            "titulo": "Buscar Canais",
            "campos": [
                {
                    "label": "Valor:",
                    "widget": "entry",
                    "global": "CANAL_BUSCA_ENTRY",
                    "connect": "buscar",
                }
            ],
        },
        "lista": {
            "global": "LIST_CANAL",
            "headers": ["Canal", "Largura", "Altura", "Compr.", "Obs."],
            "widths": [60, 60, 60, 60, 100],
        },
        "edicao": {
            "titulo_novo": "Novo Canal",
            "titulo_edit": "Editar Canal",
            "campos": [
                {
                    "label": "Valor:",
                    "widget": "entry",
                    "global": "CANAL_VALOR_ENTRY",
                    "pos": (0, 0),
                },
                {
                    "label": "Largura:",
                    "widget": "entry",
                    "global": "CANAL_LARGU_ENTRY",
                    "pos": (0, 1),
                },
                {
                    "label": "Altura:",
                    "widget": "entry",
                    "global": "CANAL_ALTUR_ENTRY",
                    "pos": (2, 0),
                },
                {
                    "label": "Comprimento total:",
                    "widget": "entry",
                    "global": "CANAL_COMPR_ENTRY",
                    "pos": (2, 1),
                },
                {
                    "label": "Observação:",
                    "widget": "entry",
                    "global": "CANAL_OBSER_ENTRY",
                    "pos": (4, 0),
                    "colspan": 2,
                },
            ],
        },
        "tipo_busca": "canal",
    },
    "espessura": {
        "titulo": "Formulário de Espessuras",
        "size": (240, 320),
        "global_form": "ESPES_FORM",
        "global_edit": "EDIT_ESP",
        "busca": {
            "titulo": "Buscar Espessuras",
            "campos": [
                {
                    "label": "Valor:",
                    "widget": "entry",
                    "global": "ESP_BUSCA_ENTRY",
                    "connect": "buscar",
                }
            ],
        },
        "lista": {"global": "LIST_ESP", "headers": ["Valor"], "widths": [180]},
        "edicao": {
            "titulo_novo": "Adicionar Espessura",
            "titulo_edit": "Editar Espessura",
            "campos": [
                {
                    "label": "Valor:",
                    "widget": "entry",
                    "global": "ESP_VALOR_ENTRY",
                    "pos": (0, 0),
                }
            ],
        },
        "tipo_busca": "espessura",
    },
}


class ButtonConfigManager:
    """Gerencia a configuração de botões para os formulários."""

    def __init__(self, config, tipo):
        """Initialize button configuration manager with config and type."""
        self.config = config
        self.tipo = tipo
        self.is_edit = getattr(g, config["global_edit"], False)
        self.tipo_operacao = config.get("tipo_busca", tipo)

    def create_button_container(self):
        """Cria o container para os botões fora do grid."""
        if self.tipo == "espessura" and self.is_edit:
            return None

        botao_container = QWidget()
        botao_layout = QHBoxLayout(botao_container)
        aplicar_medida_borda_espaco(botao_layout, 0)

        if self.is_edit:
            atualizar_btn = QPushButton("✏️ Atualizar")
            aplicar_estilo_botao(atualizar_btn, "verde")
            atualizar_btn.setShortcut(QKeySequence("Ctrl+S"))
            atualizar_btn.setToolTip("Salva as alterações no item selecionado (Ctrl+S)")
            atualizar_btn.clicked.connect(lambda: editar(self.tipo_operacao))
            botao_layout.addWidget(atualizar_btn)
        else:
            adicionar_btn = QPushButton("➕ Adicionar")
            aplicar_estilo_botao(adicionar_btn, "azul")
            adicionar_btn.setShortcut(QKeySequence("Ctrl+Return"))
            adicionar_btn.setToolTip(
                "Adiciona um novo item com os dados preenchidos (Ctrl+Enter)"
            )
            adicionar_btn.clicked.connect(lambda: adicionar(self.tipo_operacao))
            botao_layout.addWidget(adicionar_btn)

        return botao_container

    def update_form_titles(self, form_widget, frame_edicoes):
        """Atualiza os títulos do formulário e frame."""
        if not form_widget:
            return

        if self.is_edit:
            form_widget.setWindowTitle(
                f"Editar/Excluir {self.config['titulo'].split(' ')[-1]}"
            )
        else:
            if self.tipo == "espessura":
                form_widget.setWindowTitle("Adicionar Espessura")
            else:
                nome = self.config["titulo"].split(" ")[-1]
                form_widget.setWindowTitle(f"Novo {nome}")

        if frame_edicoes:
            if self.is_edit:
                frame_edicoes.setTitle(self.config["edicao"]["titulo_edit"])
            else:
                frame_edicoes.setTitle(self.config["edicao"]["titulo_novo"])

    def setup_list_connection(self):
        """Configura conexão de seleção da lista no modo edição."""
        if self.is_edit:
            list_widget = getattr(g, self.config["lista"]["global"])
            if list_widget:
                list_widget.itemSelectionChanged.connect(
                    lambda: preencher_campos(self.tipo_operacao)
                )


class FormManager:
    """Gerencia a criação e configuração de formulários."""

    def __init__(self, tipo, config, root):
        """Initialize form manager with type, config and root widget."""
        self.tipo = tipo
        self.config = config
        self.root = root

    def setup_window(self):
        """Configura a janela principal do formulário."""
        form_attr = self.config["global_form"]
        current_form = getattr(g, form_attr, None)
        if current_form:
            is_valid = getattr(Shiboken, "isValid", None)
            should_close = True
            if callable(is_valid):
                try:
                    should_close = bool(is_valid(current_form))
                except TypeError:
                    should_close = False

            if should_close:
                try:
                    current_form.close()
                    current_form.deleteLater()
                except RuntimeError:
                    pass
            setattr(g, form_attr, None)

        new_form = self._create_dialog()
        setattr(g, form_attr, new_form)
        return new_form

    def _create_dialog(self):
        """Cria o diálogo do formulário com barra de título nativa."""
        new_form = QDialog(self.root)
        is_edit = getattr(g, self.config["global_edit"], False)
        if is_edit:
            nome = self.config["titulo"].split(" ")[-1]
            titulo_janela = f"Editar/Excluir {nome}"
        else:
            if self.tipo == "espessura":
                titulo_janela = "Adicionar Espessura"
            else:
                nome = self.config["titulo"].split(" ")[-1]
                titulo_janela = f"Adicionar {nome}"
        new_form.setWindowTitle(titulo_janela)
        new_form.resize(*self.config["size"])
        new_form.setMinimumSize(*self.config["size"])

        configure_frameless_dialog(new_form, ICON_PATH)

        vlayout = QVBoxLayout(new_form)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)

        conteudo_widget = QWidget()
        vlayout.addWidget(conteudo_widget)

        grid_layout = QGridLayout(conteudo_widget)
        conteudo_widget.setLayout(grid_layout)

        new_form.conteudo_layout = grid_layout  # type: ignore[attr-defined]

        Janela.posicionar_janela(new_form, None)

        return new_form

    def config_layout_main(self, form):
        """Configura o layout principal do formulário."""
        return form.conteudo_layout

    def criar_frame_busca(self):
        """Cria o frame de busca."""
        return criar_frame_busca(self.config, self.tipo)

    def criar_widget_lista(self):
        """Cria o widget de lista."""
        return criar_lista(self.config, self.tipo)

    def criar_botao_delete(self):
        """Cria o botão de excluir se necessário."""
        is_edit = getattr(g, self.config["global_edit"], False)
        if not is_edit:
            return None

        excluir_container = QWidget()
        excluir_layout = QHBoxLayout(excluir_container)
        aplicar_medida_borda_espaco(excluir_layout, 0)

        excluir_btn = QPushButton("🗑️ Excluir")
        aplicar_estilo_botao(excluir_btn, "vermelho")
        excluir_btn.setShortcut(QKeySequence("Delete"))
        excluir_btn.setToolTip("Exclui o item selecionado permanentemente (Del)")

        tipo_operacao = self.config.get("tipo_busca", self.tipo)
        excluir_btn.clicked.connect(lambda: excluir(tipo_operacao))

        excluir_layout.addWidget(excluir_btn)
        return excluir_container

    def criar_frame_edicoes(self):
        """Cria o frame de edições se necessário."""
        is_edit = getattr(g, self.config["global_edit"], False)
        if is_edit and self.tipo == "espessura":
            return None

        return criar_frame_edicoes(self.config)


def criar_label(layout, texto, pos):
    """Cria um rótulo (QLabel) no layout especificado."""
    linha, coluna = pos
    label = QLabel(texto)
    label.setObjectName("label_titulo")
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(label, linha, coluna)
    return label


def criar_widget(layout, tipo, nome_global, pos, **kwargs):
    """Cria e configura um widget, o adiciona ao layout e o armazena em g."""
    if tipo == "entry":
        widget = QLineEdit()
    elif tipo == "combobox":
        widget = QComboBox()
    else:
        return None

    _configurar_tooltip_widget(widget, nome_global)

    colspan = kwargs.get("colspan", 1)
    rowspan = kwargs.get("rowspan", 1)
    linha, coluna = pos

    layout.addWidget(widget, linha, coluna, rowspan, colspan)
    setattr(g, nome_global, widget)
    return widget


def _configurar_tooltip_widget(widget, nome_global):
    """Configura tooltips específicos para widgets baseados no nome."""
    tooltips = {
        "MAT_NOME_ENTRY": "Digite o nome do novo material",
        "MAT_DENS_ENTRY": "Digite a densidade do material em g/cm³",
        "MAT_ESCO_ENTRY": "Digite o limite de escoamento do material em MPa",
        "MAT_ELAS_ENTRY": "Digite o módulo de elasticidade do material em GPa",
        "CANAL_VALOR_ENTRY": "Digite o valor do canal",
        "CANAL_LARGU_ENTRY": "Digite a largura do canal em milímetros",
        "CANAL_ALTUR_ENTRY": "Digite a altura do canal em milímetros",
        "CANAL_COMPR_ENTRY": "Digite o comprimento total do canal em metros",
        "CANAL_OBSER_ENTRY": "Digite observações sobre este canal",
        "ESP_VALOR_ENTRY": "Digite o valor da espessura em milímetros",
        "DED_VALOR_ENTRY": "Digite o valor da dedução em milímetros",
        "DED_OBSER_ENTRY": "Digite observações sobre esta dedução",
        "DED_FORCA_ENTRY": "Digite a força necessária em toneladas por metro (t/m)",
        "MAT_BUSCA_ENTRY": "Digite parte do nome do material para buscar",
        "ESP_BUSCA_ENTRY": "Digite parte da espessura para buscar",
        "CANAL_BUSCA_ENTRY": "Digite parte do valor do canal para buscar",
        "DED_MATER_COMB": "Selecione o material para filtrar deduções",
        "DED_ESPES_COMB": "Selecione a espessura para filtrar deduções",
        "DED_CANAL_COMB": "Selecione o canal para filtrar deduções",
    }

    if nome_global in tooltips:
        widget.setToolTip(tooltips[nome_global])


def criar_frame_busca(config, tipo):
    """Cria o frame de busca baseado na configuração."""
    frame_busca = QGroupBox(config["busca"]["titulo"])
    layout = QGridLayout(frame_busca)
    aplicar_medida_borda_espaco(layout)

    tipo_busca = config.get("tipo_busca", tipo)

    for col, campo in enumerate(config["busca"]["campos"]):
        _criar_campo_busca(layout, campo, col, tipo_busca)

    _criar_botao_limpar_busca(layout, len(config["busca"]["campos"]), tipo_busca)

    return frame_busca


def _criar_campo_busca(layout, campo, col, tipo_busca):
    """Cria um campo individual de busca."""
    criar_label(layout, campo["label"], (0, col))
    widget = criar_widget(layout, campo["widget"], campo["global"], (1, col))

    configurar_conexoes_busca(widget, campo, tipo_busca)


def _criar_botao_limpar_busca(layout, col, tipo_busca):
    """Cria o botão de limpar busca."""
    limpar_btn = QPushButton("🧹 Limpar")
    aplicar_estilo_botao(limpar_btn, "amarelo")
    limpar_btn.setShortcut(QKeySequence("Ctrl+R"))
    limpar_btn.setToolTip("Limpa os campos de busca e recarrega a lista (Ctrl+R)")
    limpar_btn.clicked.connect(lambda: limpar_busca(tipo_busca))
    layout.addWidget(limpar_btn, 1, col)


def configurar_conexoes_busca(widget, campo_config, tipo_busca):
    """Configura conexões de busca para widgets."""
    if campo_config.get("connect") != "buscar":
        return

    if campo_config["widget"] == "entry":
        widget.textChanged.connect(lambda _, tb=tipo_busca: buscar_debounced(tb))
    elif campo_config["widget"] == "combobox":
        widget.currentTextChanged.connect(lambda _, tb=tipo_busca: buscar_debounced(tb))


def criar_lista(config, tipo):
    """Cria a lista/tabela baseada na configuração."""
    table_widget = QTableWidget()
    table_widget.setColumnCount(len(config["lista"]["headers"]))
    table_widget.setHorizontalHeaderLabels(config["lista"]["headers"])
    table_widget.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
    table_widget.setAlternatingRowColors(True)
    table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table_widget.verticalHeader().setVisible(False)

    aplicar_estilo_table_widget(table_widget)

    header = table_widget.horizontalHeader()
    for i, width in enumerate(config["lista"]["widths"]):
        header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        table_widget.setColumnWidth(i, width)

    setattr(g, config["lista"]["global"], table_widget)

    tipo_lista = config.get("tipo_busca", tipo)
    listar(tipo_lista)

    return table_widget


def criar_frame_edicoes(config):
    """Cria o frame de edições baseado na configuração."""
    is_edit = getattr(g, config["global_edit"], False)
    titulo = (
        config["edicao"]["titulo_edit"] if is_edit else config["edicao"]["titulo_novo"]
    )

    frame_edicoes = QGroupBox(titulo)
    frame_edicoes.setObjectName("label_titulo")
    layout = QGridLayout(frame_edicoes)
    aplicar_medida_borda_espaco(layout)

    for campo in config["edicao"]["campos"]:
        _criar_campo_edicao(layout, campo)

    return frame_edicoes


def _criar_campo_edicao(layout, campo):
    """Cria um campo individual de edição."""
    pos_label = campo["pos"]
    pos_widget = (pos_label[0] + 1, pos_label[1])

    criar_label(layout, campo["label"], pos_label)

    colspan = campo.get("colspan", 1)
    criar_widget(layout, campo["widget"], campo["global"], pos_widget, colspan=colspan)


def configurar_botoes(config, tipo):
    """Configura os botões baseado na configuração."""
    button_manager = ButtonConfigManager(config, tipo)

    botao_container = button_manager.create_button_container()

    form_widget = getattr(g, button_manager.config["global_form"])
    button_manager.update_form_titles(form_widget, None)

    button_manager.setup_list_connection()

    return botao_container


def main(tipo, root):
    """Função principal universal para todos os formulários."""
    if tipo not in FORM_CONFIGS:
        raise ValueError(f"Tipo '{tipo}' não suportado")

    config = FORM_CONFIGS[tipo]
    gerenciador_form = FormManager(tipo, config, root)

    novo_form = gerenciador_form.setup_window()
    layout_principal = gerenciador_form.config_layout_main(novo_form)

    _config_componentes_form(gerenciador_form, layout_principal)

    _executar_pos_inicio(config, tipo)

    novo_form.show()


def _config_componentes_form(gerenciador_form, layout):
    """Configura os componentes do formulário."""
    aplicar_medida_borda_espaco(layout, 10)

    frame_busca = gerenciador_form.criar_frame_busca()
    layout.addWidget(frame_busca, 0, 0)

    lista_widget = gerenciador_form.criar_widget_lista()
    layout.addWidget(lista_widget, 1, 0)

    excluir_container = gerenciador_form.criar_botao_delete()
    current_row = 2
    if excluir_container:
        layout.addWidget(excluir_container, current_row, 0)
        current_row += 1

    frame_edicoes = gerenciador_form.criar_frame_edicoes()
    if frame_edicoes:
        layout.addWidget(frame_edicoes, current_row, 0)
        current_row += 1

    botao_container = configurar_botoes(gerenciador_form.config, gerenciador_form.tipo)
    if botao_container:
        layout.addWidget(botao_container, current_row, 0)


def _executar_pos_inicio(config, tipo):
    """Executa pós-inicialização se necessário."""
    if "post_init" in config:
        config["post_init"]()

    tipo_lista = config.get("tipo_busca", tipo)
    listar(tipo_lista)


if __name__ == "__main__":
    main("material", None)
