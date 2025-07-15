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
from src.config import globals as g
# Imports no topo para evitar imports dentro de funções
try:
    import qdarktheme
    QDARKTHEME_DISPONIVEL = True
except ImportError:
    qdarktheme = None
    QDARKTHEME_DISPONIVEL = False

# Constantes seguindo convenção UPPER_CASE
TEMA_ATUAL_PADRAO = "dark"

# Constantes para widgets auto-ajustáveis
g.WIDGET_MAX_HEIGHT = 20  # Manter altura fixa para consistência
g.WIDGET_MIN_WIDTH = 60  # Largura mínima para garantir usabilidade
WIDGET_PADDING = "2px 4px"  # Padding interno uniforme


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
            print("qdarktheme não está disponível.")
            return

        css_correcao = obter_css_correcao_widgets()

        try:
            if hasattr(qdarktheme, "enable"):
                qdarktheme.enable(theme=nome_tema, additional_qss=css_correcao)
            elif hasattr(qdarktheme, "setup_theme"):
                qdarktheme.setup_theme(nome_tema, additional_qss=css_correcao)
            else:
                print("qdarktheme não possui métodos conhecidos para aplicar tema.")
                return

            self.tema_atual = nome_tema

            # Atualizar checkboxes dos menus se registrados
            if self.temas_actions:
                for tema, action in self.temas_actions.items():
                    if hasattr(action, 'setChecked'):
                        action.setChecked(tema == nome_tema)

            print(f"Tema '{nome_tema}' aplicado com sucesso.")

        except ImportError as e:
            print(f"Erro ao importar qdarktheme: {e}")
        except (AttributeError, TypeError, ValueError) as e:
            print(f"Erro ao aplicar tema: {e}")

    def aplicar_tema_inicial(self, tema=None):
        """
        Aplica o tema inicial na inicialização da aplicação.

        Args:
            tema: Nome do tema inicial (opcional, usa padrão se None)
        """
        if tema is None:
            tema = TEMA_ATUAL_PADRAO

        if not QDARKTHEME_DISPONIVEL:
            print("qdarktheme não encontrado. O tema escuro não será aplicado.")
            return

        try:
            css_correcao = obter_css_correcao_widgets()

            if hasattr(qdarktheme, "setup_theme"):
                qdarktheme.setup_theme(tema, additional_qss=css_correcao)
            elif hasattr(qdarktheme, "enable"):
                qdarktheme.enable(theme=tema, additional_qss=css_correcao)

            self.tema_atual = tema
            print(f"Tema inicial '{tema}' aplicado com correções de CSS.")

        except (AttributeError, TypeError, ValueError) as e:
            print(f"Erro ao aplicar tema inicial: {e}")


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
        color: #ffffff;
        background-color: #2d2d2d;
        border: 1px solid #555555;
        border-radius: 3px;
        padding: 4px 6px;
        font-size: 9pt;
        font-family: inherit;
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


# Funções para estilos de botões coloridos
def obter_estilo_botao_cinza():
    """Retorna o estilo CSS para botões cinza."""
    return """
    QPushButton {
        background-color: #9e9e9e;
        color: white;
        border: none;
        padding: 4px 8px;
        font-weight: bold;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #757575;
    }
    QPushButton:pressed {
        background-color: #616161;
    }
    """


def obter_estilo_botao_azul():
    """Retorna o estilo CSS para botões azuis."""
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


def obter_estilo_botao_amarelo():
    """Retorna o estilo CSS para botões amarelos."""
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


def obter_estilo_botao_vermelho():
    """Retorna o estilo CSS para botões vermelhos."""
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


def obter_estilo_botao_verde():
    """Retorna o estilo CSS para botões verdes."""
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
