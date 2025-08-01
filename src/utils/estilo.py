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

# Imports no topo para evitar imports dentro de funções
try:
    import qdarktheme
    QDARKTHEME_DISPONIVEL = True
except ImportError:
    qdarktheme = None
    QDARKTHEME_DISPONIVEL = False

# Configurar logger
logger = logging.getLogger(__name__)

# Constantes seguindo convenção UPPER_CASE
TEMA_ATUAL_PADRAO = "dark"

# Constantes para widgets auto-ajustáveis
WIDGET_HEIGHT_PADRAO = 20  # Altura fixa para consistência
WIDGET_MIN_WIDTH_PADRAO = 60  # Largura mínima para garantir usabilidade
WIDGET_PADDING = "2px 4px"  # Padding interno uniforme

# Definir constantes globais
g.WIDGET_MAX_HEIGHT = WIDGET_HEIGHT_PADRAO
g.WIDGET_MIN_WIDTH = WIDGET_MIN_WIDTH_PADRAO


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
                    "qdarktheme não possui métodos conhecidos para aplicar tema.")
                return

            self.tema_atual = nome_tema

            # Atualizar checkboxes dos menus se registrados
            if self.temas_actions:
                for tema, action in self.temas_actions.items():
                    if hasattr(action, 'setChecked'):
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
                "qdarktheme não encontrado. O tema escuro não será aplicado.")
            return

        try:
            css_correcao = obter_css_correcao_widgets()

            if hasattr(qdarktheme, "setup_theme"):
                qdarktheme.setup_theme(tema, additional_qss=css_correcao)
            elif hasattr(qdarktheme, "enable"):
                qdarktheme.enable(theme=tema, additional_qss=css_correcao)

            self.tema_atual = tema
            logger.info(
                "Tema inicial '%s' aplicado com correções de CSS.", tema)

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
    return """
    QComboBox { 
        min-height: 1em; 
        max-height: {g.WIDGET_MAX_HEIGHT}px; 
        padding: 2px 4px; 
        font-size: 10pt;
    }
    QLineEdit { 
        min-height: 1em; 
        max-height: {g.WIDGET_MAX_HEIGHT}px; 
        padding: 2px 4px; 
        font-size: 10pt;
    }
    QLabel { 
        min-height: 1em;
        padding: 2px; 
        font-size: 10pt;
    }
    QGroupBox::title {
        font-size: 10pt;
        padding: 2px;
    }

    QToolTip {
        color: white;
        background-color: #2d2d2d;
        border-radius: 3px;
        padding: 4px 6px;
        font-size: 9pt;
        opacity: 240;
    }
    """


def obter_css_widgets_auto_ajustaveis():
    """
    Retorna CSS para widgets com largura auto-ajustável.

    Returns:
        dict: CSS para cada tipo de widget com largura flexível
    """
    return {
        'combobox': f"""
            QComboBox {{
                min-width: {g.WIDGET_MIN_WIDTH}px;
                min-height: 1em; 
                max-height: {g.WIDGET_MAX_HEIGHT}px;
                padding: {WIDGET_PADDING};
                font-size: 10pt;
            }}
        """,
        'lineedit': f"""
            QLineEdit {{
                min-width: {g.WIDGET_MIN_WIDTH}px;
                min-height: 1em; 
                max-height: {g.WIDGET_MAX_HEIGHT}px;
                padding: {WIDGET_PADDING};
                font-size: 10pt;
            }}
        """
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
        'g.WIDGET_MAX_HEIGHT': g.WIDGET_MAX_HEIGHT,
        'g.WIDGET_MIN_WIDTH': g.WIDGET_MIN_WIDTH,
        'horizontal_spacing': 5,
        'vertical_spacing': 3
    }


def configurar_layout_flexivel(layout):
    """
    Configura um layout para ter widgets auto-ajustáveis.

    Args:
        layout: Layout a ser configurado
    """
    config = obter_configuracao_layout_flexivel()

    # Configurar colunas com expansão proporcional
    for col in range(4):
        layout.setColumnStretch(col, 1)  # Permitir expansão igual

    # Configurar espaçamento
    layout.setHorizontalSpacing(config['horizontal_spacing'])
    layout.setVerticalSpacing(config['vertical_spacing'])


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
    if hasattr(g, 'BARRA_TITULO') and g.BARRA_TITULO:
        g.BARRA_TITULO.set_tema(nome_tema)


def aplicar_tema_inicial(tema=None):
    """Função de conveniência para aplicar tema inicial."""
    gerenciador_temas.aplicar_tema_inicial(tema)


def obter_tema_atual():
    """Função de conveniência para obter tema atual."""
    return gerenciador_temas.obter_tema_atual()


# Configurações de cores para botões
BUTTON_COLORS = {
    'cinza': {
        'normal': '#9e9e9e',
        'hover': '#757575',
        'pressed': '#616161',
        'text': 'white'
    },
    'azul': {
        'normal': '#2196f3',
        'hover': '#1976d2',
        'pressed': '#1565c0',
        'text': 'white'
    },
    'amarelo': {
        'normal': '#ffd93d',
        'hover': '#ffcc02',
        'pressed': '#e6b800',
        'text': '#333'
    },
    'vermelho': {
        'normal': '#ff6b6b',
        'hover': '#ff5252',
        'pressed': '#e53935',
        'text': 'white'
    },
    'verde': {
        'normal': '#4caf50',
        'hover': '#45a049',
        'pressed': '#3d8b40',
        'text': 'white'
    }
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
        cor = 'cinza'  # fallback para cor padrão

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


# Funções de compatibilidade (mantidas para não quebrar código existente)
def obter_estilo_botao_cinza():
    """Retorna o estilo CSS para botões cinza."""
    return obter_estilo_botao('cinza')


def obter_estilo_botao_azul():
    """Retorna o estilo CSS para botões azuis."""
    return obter_estilo_botao('azul')


def obter_estilo_botao_amarelo():
    """Retorna o estilo CSS para botões amarelos."""
    return obter_estilo_botao('amarelo')


def obter_estilo_botao_vermelho():
    """Retorna o estilo CSS para botões vermelhos."""
    return obter_estilo_botao('vermelho')


def obter_estilo_botao_verde():
    """Retorna o estilo CSS para botões verdes."""
    return obter_estilo_botao('verde')


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
