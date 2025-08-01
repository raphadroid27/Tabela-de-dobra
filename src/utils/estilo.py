"""
Este módulo fornece funções utilitárias para retornar estilos CSS personalizados para
botões do PySide6 (QPushButton) em diferentes cores temáticas, além de gerenciar
temas globais da aplicação usando qdarktheme.

Funcionalidades:
- Gerenciamento de temas qdarktheme
- Estilos CSS para botões coloridos
- Widgets auto-ajustáveis para interface
- Correções de CSS para compatibilidade com temas
"""

import logging

from src.config import globals as g

try:
    import qdarktheme

    QDARKTHEME_DISPONIVEL = True
except ImportError:
    qdarktheme = None
    QDARKTHEME_DISPONIVEL = False

logger = logging.getLogger(__name__)

TEMA_ATUAL_PADRAO = "dark"

ALTURA_PADRAO_COMPONENTE = 20
LARGURA_MINIMA_COMPONENTE = 60
PADDING_INTERNO_COMPONENTE = "2px 4px"

ALTURA_PADRAO_BOTAO = 25
LARGURA_MINIMA_BOTAO = 20


class GerenciadorTemas:
    """Classe para gerenciar temas da aplicação de forma organizada."""

    def __init__(self):
        """Inicializa o gerenciador de temas."""
        self.tema_atual = TEMA_ATUAL_PADRAO
        self.temas_actions = {}

    def registrar_tema_actions(self, actions_dict):
        """
        Registra o dicionário de ações dos temas para controle de estado.

        Args:
            actions_dict: Dicionário com ações dos temas {nome_tema: QAction}
        """
        self.temas_actions = actions_dict

    def obter_tema_atual(self):
        """
        Retorna o tema atualmente ativo.

        Returns:
            str: Nome do tema atual
        """
        return self.tema_atual

    def aplicar_tema_qdarktheme(self, nome_tema):
        """
        Aplica um tema qdarktheme com CSS de correção para widgets desproporcionais.

        Args:
            nome_tema: Nome do tema a ser aplicado ("dark", "light", "auto")
        """
        if not QDARKTHEME_DISPONIVEL:
            logger.warning("qdarktheme não está disponível.")
            return

        css_correcao = obter_css_correcao_widgets()

        try:
            if hasattr(qdarktheme, "enable"):
                qdarktheme.enable(theme=nome_tema, additional_qss=css_correcao)
            elif hasattr(qdarktheme, "setup_theme"):
                qdarktheme.setup_theme(nome_tema, additional_qss=css_correcao)
            else:
                logger.error(
                    "qdarktheme não possui métodos conhecidos para aplicar tema."
                )
                return

            self.tema_atual = nome_tema

            # Atualizar checkboxes dos menus se registrados
            if self.temas_actions:
                for tema, action in self.temas_actions.items():
                    if hasattr(action, "setChecked"):
                        action.setChecked(tema == nome_tema)

            logger.info("Tema '%s' aplicado com sucesso.", nome_tema)

        except ImportError as e:
            logger.error("Erro ao importar qdarktheme: %s", e)
        except (AttributeError, TypeError, ValueError) as e:
            logger.error("Erro ao aplicar tema: %s", e)

    def aplicar_tema_inicial(self, tema=None):
        """
        Aplica o tema inicial na inicialização da aplicação.

        Args:
            tema: Nome do tema inicial (opcional, usa padrão se None)
        """
        if tema is None:
            tema = TEMA_ATUAL_PADRAO

        if not QDARKTHEME_DISPONIVEL:
            logger.warning(
                "qdarktheme não encontrado. O tema escuro não será aplicado."
            )
            return

        try:
            css_correcao = obter_css_correcao_widgets()

            if hasattr(qdarktheme, "setup_theme"):
                qdarktheme.setup_theme(tema, additional_qss=css_correcao)
            elif hasattr(qdarktheme, "enable"):
                qdarktheme.enable(theme=tema, additional_qss=css_correcao)

            self.tema_atual = tema
            logger.info("Tema inicial '%s' aplicado com correções de CSS.", tema)

        except (AttributeError, TypeError, ValueError) as e:
            logger.error("Erro ao aplicar tema inicial: %s", e)


# Instância global do gerenciador
gerenciador_temas = GerenciadorTemas()


def obter_css_correcao_widgets():
    """
    Retorna CSS para corrigir tamanhos desproporcionais dos widgets
    quando usado com qdarktheme.

    Returns:
        str: CSS para correção de tamanhos
    """
    return f"""
    QComboBox {{
        min-height: 1em;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: 2px 4px;
        font-size: 10pt;
    }}
    QLineEdit {{
        min-height: 1em;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: 2px 4px;
        font-size: 10pt;
    }}
    QLabel {{
        min-height: 1em;
        padding: 2px;
        font-size: 10pt;
    }}
    QGroupBox::title {{
        font-size: 10pt;
        padding: 2px;
    }}

    QToolTip {{
        color: white;
        background-color: #2d2d2d;
        border-radius: 3px;
        padding: 4px 6px;
        font-size: 9pt;
        opacity: 240;
    }}
    """


def obter_css_widgets_auto_ajustaveis():
    """
    Retorna CSS para widgets com largura auto-ajustável.

    Returns:
        dict: CSS para cada tipo de widget com largura flexível
    """
    return {
        "combobox": f"""
            QComboBox {{
                min-width: {LARGURA_MINIMA_COMPONENTE}px;
                min-height: 1em; 
                max-height: {ALTURA_PADRAO_COMPONENTE}px;
                padding: {PADDING_INTERNO_COMPONENTE};
                font-size: 10pt;
            }}
        """,
        "lineedit": f"""
            QLineEdit {{
                min-width: {LARGURA_MINIMA_COMPONENTE}px;
                min-height: 1em; 
                max-height: {ALTURA_PADRAO_COMPONENTE}px;
                padding: {PADDING_INTERNO_COMPONENTE};
                font-size: 10pt;
            }}
        """,
    }


def aplicar_estilo_widget_auto_ajustavel(widget, tipo_widget):
    """
    Aplica estilo auto-ajustável aos widgets do cabeçalho.
    Mantém altura fixa mas permite largura flexível.

    Args:
        widget: Widget a receber o estilo
        tipo_widget: Tipo do widget ('combobox', 'lineedit')
    """
    estilos = obter_css_widgets_auto_ajustaveis()
    if tipo_widget in estilos:
        widget.setStyleSheet(estilos[tipo_widget])


def obter_configuracao_layout_flexivel():
    """
    Retorna configurações de layout para widgets auto-ajustáveis.

    Returns:
        dict: Configurações de layout flexível
    """
    return {
        "altura_padrao": ALTURA_PADRAO_COMPONENTE,
        "largura_minima": LARGURA_MINIMA_COMPONENTE,
        "horizontal_spacing": 5,
        "vertical_spacing": 3,
    }


def configurar_layout_flexivel(layout):
    """
    Configura um layout para ter widgets auto-ajustáveis.

    Args:
        layout: Layout a ser configurado
    """
    config = obter_configuracao_layout_flexivel()

    for col in range(4):
        layout.setColumnStretch(col, 1)

    layout.setHorizontalSpacing(config["horizontal_spacing"])
    layout.setVerticalSpacing(config["vertical_spacing"])


def obter_temas_disponiveis():
    """
    Retorna lista de temas disponíveis do qdarktheme.

    Returns:
        list: Lista de temas disponíveis
    """
    if not QDARKTHEME_DISPONIVEL:
        return ["dark", "light"]

    if hasattr(qdarktheme, "get_themes"):
        return qdarktheme.get_themes()
    return ["dark", "light", "auto"]


# Funções de conveniência para compatibilidade com código existente
def registrar_tema_actions(actions_dict):
    """Função de conveniência para registrar ações de tema."""
    gerenciador_temas.registrar_tema_actions(actions_dict)


def aplicar_tema_qdarktheme(nome_tema):
    """Função de conveniência para aplicar tema."""
    gerenciador_temas.aplicar_tema_qdarktheme(nome_tema)
    # Atualizar barra de título customizada, se existir
    if hasattr(g, "BARRA_TITULO") and g.BARRA_TITULO:
        g.BARRA_TITULO.set_tema(nome_tema)


def aplicar_tema_inicial(tema=None):
    """Função de conveniência para aplicar tema inicial."""
    gerenciador_temas.aplicar_tema_inicial(tema)


def obter_tema_atual():
    """Função de conveniência para obter tema atual."""
    return gerenciador_temas.obter_tema_atual()


# Configurações de cores para botões
BUTTON_COLORS = {
    "cinza": {
        "normal": "#9e9e9e",
        "hover": "#757575",
        "pressed": "#616161",
        "text": "white",
    },
    "azul": {
        "normal": "#2196f3",
        "hover": "#1976d2",
        "pressed": "#1565c0",
        "text": "white",
    },
    "amarelo": {
        "normal": "#ffd93d",
        "hover": "#ffcc02",
        "pressed": "#e6b800",
        "text": "#333",
    },
    "vermelho": {
        "normal": "#ff6b6b",
        "hover": "#ff5252",
        "pressed": "#e53935",
        "text": "white",
    },
    "verde": {
        "normal": "#4caf50",
        "hover": "#45a049",
        "pressed": "#3d8b40",
        "text": "white",
    },
}


def obter_estilo_botao(cor: str) -> str:
    """
    Retorna o estilo CSS para botões com a cor especificada.

    Args:
        cor: Uma das cores disponíveis: 'cinza', 'azul', 'amarelo', 'vermelho', 'verde'

    Returns:
        String CSS para aplicar ao botão
    """
    if cor not in BUTTON_COLORS:
        cor = "cinza"  # fallback para cor padrão

    colors = BUTTON_COLORS[cor]
    return f"""
    QPushButton {{
        background-color: {colors['normal']};
        color: {colors['text']};
        border: none;
        padding: 4px 8px;
        font-weight: bold;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background-color: {colors['hover']};
    }}
    QPushButton:pressed {{
        background-color: {colors['pressed']};
    }}
    """


# Funções de compatibilidade removidas - usar aplicar_estilo_botao() diretamente


def obter_estilo_progress_bar():
    """Retorna o estilo CSS para a barra de progresso."""
    return """
        QProgressBar {
            border: 1px solid #555;
            border-radius: 5px;
            text-align: center;
            height: 10px;
        }
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 4px;
        }
    """


def aplicar_estilo_botao(botao, cor: str, altura: int = None, largura_min: int = None):
    """Aplica estilo completo de botão de forma conveniente.

    Args:
        botao: O botão QPushButton a ser estilizado
        cor: Cor do botão ('cinza', 'azul', 'amarelo', 'vermelho', 'verde')
        altura: Altura do botão (padrão: ALTURA_PADRAO_BOTAO)
        largura_min: Largura mínima do botão (padrão: LARGURA_MINIMA_BOTAO)
    """
    if not hasattr(botao, "setStyleSheet"):
        return

    botao.setStyleSheet(obter_estilo_botao(cor))

    altura_final = altura if altura is not None else ALTURA_PADRAO_BOTAO
    largura_final = largura_min if largura_min is not None else LARGURA_MINIMA_BOTAO

    if hasattr(botao, "setFixedHeight"):
        botao.setFixedHeight(altura_final)

    if hasattr(botao, "setMinimumWidth"):
        botao.setMinimumWidth(largura_final)


# Função aplicar_estilo_componente removida - não utilizada no projeto


def aplicar_estilo_checkbox(checkbox, altura: int = None):
    """Aplica estilo padronizado para checkboxes.

    Args:
        checkbox: O checkbox QCheckBox a ser configurado
        altura: Altura do checkbox (padrão: CHECKBOX_ALTURA_PADRAO)
    """
    if not hasattr(checkbox, "setFixedHeight"):
        return

    altura_final = altura if altura is not None else ALTURA_PADRAO_COMPONENTE
    checkbox.setFixedHeight(altura_final)
