"""
Formulário Universal para todos os tipos de CRUD do sistema.

Este módulo unifica todos os formulários de adição/edição, eliminando duplicação de código
e facilitando manutenção através de configurações centralizadas.

Versão atualizada com botões de ação fora do grid para melhor organização visual.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QVBoxLayout,
    QWidget,

)

from src.components.barra_titulo import BarraTitulo
from src.config import globals as g
from src.utils.controlador import (adicionar, buscar, editar, excluir, preencher_campos)
from src.utils.estilo import (
    ALTURA_PADRAO_COMPONENTE,
    aplicar_estilo_botao,
    obter_tema_atual,
)
from src.utils.interface import (
    atualizar_comboboxes_formulario,
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
                "Força [Ton/m]",
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
                    "label": "Força [Ton/m]:",
                    "widget": "entry",
                    "global": "DED_FORCA_ENTRY",
                    "pos": (0, 2),
                },
            ],
        },
        "post_init": lambda: atualizar_comboboxes_formulario(
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
            atualizar_btn.clicked.connect(lambda: editar(self.tipo_operacao))
            botao_layout.addWidget(atualizar_btn)
        else:
            adicionar_btn = QPushButton("➕ Adicionar")
            aplicar_estilo_botao(adicionar_btn, "azul")
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
        self.tipo = tipo
        self.config = config
        self.root = root
        self.main_layout = None

    def setup_window(self):
        """Configura a janela principal do formulário."""
        form_attr = self.config["global_form"]
        current_form = getattr(g, form_attr, None)
        if current_form:
            current_form.close()

        new_form, main_layout = self._create_dialog()
        self.main_layout = main_layout
        setattr(g, form_attr, new_form)
        return new_form

    def _create_dialog(self):
        """
        Cria o diálogo do formulário com barra de título customizada.
        Retorna uma tupla (QDialog, QGridLayout)
        """
        new_form = QDialog(self.root)
        new_form.setWindowTitle(self.config["titulo"])
        new_form.resize(*self.config["size"])
        new_form.setFixedSize(*self.config["size"])

        new_form.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        new_form.setWindowIcon(QIcon(ICON_PATH))

        vlayout = QVBoxLayout(new_form)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)

        is_edit = getattr(g, self.config["global_edit"], False)
        if is_edit:
            nome = self.config["titulo"].split(" ")[-1]
            barra_titulo = f"Editar/Excluir {nome}"
        else:
            if self.tipo == "espessura":
                barra_titulo = "Adicionar Espessura"
            else:
                nome = self.config["titulo"].split(" ")[-1]
                barra_titulo = f"Adicionar {nome}"

        barra = BarraTitulo(new_form, tema=obter_tema_atual())
        barra.titulo.setText(barra_titulo)
        vlayout.addWidget(barra)

        conteudo_widget = QWidget()
        vlayout.addWidget(conteudo_widget)

        grid_layout = QGridLayout(conteudo_widget)
        conteudo_widget.setLayout(grid_layout)

        Janela.aplicar_no_topo(new_form)
        Janela.posicionar_janela(new_form, None)

        return new_form, grid_layout

    def config_layout_main(self):
        """Configura o layout principal do formulário."""
        return self.main_layout

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
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(label, linha, coluna)
    return label


def criar_widget(layout, tipo, nome_global, pos, **kwargs) -> QWidget | None:
    """
    Cria e configura um widget, o adiciona ao layout e o armazena em g.
    Esta função foi corrigida para ser mais robusta e compatível com type checking.
    """
    # Declara a variável `widget` para que possa conter QLineEdit, QComboBox ou None.
    widget: QLineEdit | QComboBox | None = None

    if tipo == "entry":
        widget = QLineEdit()
    elif tipo == "combobox":
        widget = QComboBox()

    # Se o tipo de widget não for suportado, retorna None imediatamente.
    if widget is None:
        return None

    # Agora é seguro chamar métodos no widget, pois sabemos que não é None.
    widget.setFixedHeight(ALTURA_PADRAO_COMPONENTE)

    colspan = kwargs.get("colspan", 1)
    rowspan = kwargs.get("rowspan", 1)
    linha, coluna = pos

    layout.addWidget(widget, linha, coluna, rowspan, colspan)
    setattr(g, nome_global, widget)
    return widget


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

    # Configurar conexões
    if widget:
        configurar_conexoes_busca(widget, campo, tipo_busca)


def _criar_botao_limpar_busca(layout, col, tipo_busca):
    """Cria o botão de limpar busca."""
    limpar_btn = QPushButton("🧹 Limpar")
    aplicar_estilo_botao(limpar_btn, "amarelo")
    limpar_btn.clicked.connect(lambda: limpar_busca(tipo_busca))
    layout.addWidget(limpar_btn, 1, col)


def configurar_conexoes_busca(widget, campo_config, tipo_busca):
    """Configura conexões de busca para widgets."""
    if campo_config.get("connect") != "buscar":
        return

    if isinstance(widget, QLineEdit):
        widget.textChanged.connect(lambda _, tb=tipo_busca: buscar(tb))
    elif isinstance(widget, QComboBox):
        widget.currentTextChanged.connect(lambda _, tb=tipo_busca: buscar(tb))


def criar_lista(config, tipo):
    """Cria a lista/árvore baseada na configuração."""
    tree_widget = QTreeWidget()
    tree_widget.setHeaderLabels(config["lista"]["headers"])
    tree_widget.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
    tree_widget.setRootIsDecorated(False)

    for i, width in enumerate(config["lista"]["widths"]):
        tree_widget.setColumnWidth(i, width)

    setattr(g, config["lista"]["global"], tree_widget)

    tipo_lista = config.get("tipo_busca", tipo)
    listar(tipo_lista)

    return tree_widget


def criar_frame_edicoes(config):
    """Cria o frame de edições baseado na configuração."""
    is_edit = getattr(g, config["global_edit"], False)
    titulo = (
        config["edicao"]["titulo_edit"] if is_edit else config["edicao"]["titulo_novo"]
    )

    frame_edicoes = QGroupBox(titulo)
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
    layout_principal = gerenciador_form.config_layout_main()

    if layout_principal:
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


# Funções de compatibilidade para manter a API existente
def form_deducao_main(root):
    """Wrapper para manter compatibilidade com form_deducao."""
    main("deducao", root)


def form_material_main(root):
    """Wrapper para manter compatibilidade com form_material."""
    main("material", root)


def form_canal_main(root):
    """Wrapper para manter compatibilidade com form_canal."""
    main("canal", root)


def form_espessura_main(root):
    """Wrapper para manter compatibilidade com form_espessura."""
    main("espessura", root)


if __name__ == "__main__":
    print("Arquivo form_universal.py carregado e pronto para uso.")
