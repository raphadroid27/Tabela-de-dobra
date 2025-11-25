"""Este módulo fornece funções utilitárias para retornar estilos CSS personalizados.

Fornece estilos para botões do PySide6 (QPushButton) em diferentes cores temáticas.

Funcionalidades:
- Estilos CSS para botões coloridos
- Widgets auto-ajustáveis para interface
- Correções de CSS para compatibilidade
- Gerenciamento centralizado de temas
"""

import logging

from PySide6.QtGui import QColor

from .theme_manager import theme_manager

logger = logging.getLogger(__name__)

TEMA_ATUAL_PADRAO = "light"

# Constantes de layout e estilo
ALTURA_PADRAO_COMPONENTE = 20
LARGURA_MINIMA_COMPONENTE = 70
PADDING_INTERNO_COMPONENTE = "2px 4px"
ALTURA_PADRAO_BOTAO = 25
LARGURA_MINIMA_BOTAO = 20

COR_FUNDO_BRANCO = "#f0f0f0"
COR_FUNDO_ESCURO = "#161719"
COR_FUNDO_CLARO = "#f8f9fa"

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
    "laranja": {
        "normal": "#ff9800",
        "hover": "#fb8c00",
        "pressed": "#f57c00",
        "text": "white",
    },
}


class GerenciadorTemas:
    """Classe para gerenciar temas da aplicação de forma organizada."""

    def __init__(self):
        """Inicializa o gerenciador de temas."""
        self.tema_atual = theme_manager.current_mode
        self.temas_actions = {}
        self.accent_color = QColor(0, 122, 204)  # Azul padrão
        # Registra listener para sincronizar ações do menu quando o tema mudar
        try:
            theme_manager.register_listener(self._on_tema_alterado)
        except AttributeError:
            # Se o theme_manager não expor register_listener por algum motivo,
            # ignoramos a falha — a sincronização será feita quando
            # `registrar_tema_actions` for chamado.
            pass

    def registrar_tema_actions(self, actions_dict):
        """
        Registra o dicionário de ações dos temas para controle de estado.

        Args:
            actions_dict: Dicionário com ações dos temas {nome_tema: QAction}
        """
        self.temas_actions = actions_dict
        # Atualiza imediatamente o estado dos checkboxes com base no tema atual
        self._atualizar_checks()

    def _on_tema_alterado(self, novo_tema: str) -> None:
        """Callback chamado pelo theme_manager quando o tema é alterado.

        Atualiza o estado interno e sincroniza os checkboxes registrados.
        """
        self.tema_atual = novo_tema
        self._atualizar_checks()

    def _atualizar_checks(self) -> None:
        """Marca/desmarca ações de menu registradas conforme o tema atual."""
        if not self.temas_actions:
            return
        for tema, action in self.temas_actions.items():
            try:
                if hasattr(action, "setChecked"):
                    action.setChecked(tema == self.tema_atual)
            except (AttributeError, RuntimeError, TypeError):
                # Segurança: não permitir que um erro ao atualizar um action
                # interrompa o fluxo da aplicação.
                logger.debug("Falha ao atualizar estado de action para tema %s", tema)

    def obter_tema_atual(self):
        """
        Retorna o tema epigeneticamente ativo.

        Returns:
            str: Nome do tema atual
        """
        return theme_manager.current_mode

    def aplicar_tema_inicial(self, tema=None):
        """
        Aplica o tema inicial na inicialização da aplicação.

        Args:
            tema: Nome do tema inicial (opcional, usa padrão se None)
        """
        if tema is None:
            tema = TEMA_ATUAL_PADRAO

        theme_manager.apply_theme(tema)
        self.tema_atual = tema
        logger.info("Tema inicial '%s' aplicado.", tema)


# Instância global do gerenciador
gerenciador_temas = GerenciadorTemas()


def obter_css_correcao_widgets():
    """
    Retorna CSS para corrigir tamanhos desproporcionais dos widgets.
    Nota: Os estilos principais agora são gerenciados pelo theme_manager.

    Returns:
        str: CSS para correção de tamanhos (compatibilidade)
    """
    # Os estilos principais agora são aplicados globalmente pelo theme_manager
    # Esta função retorna apenas estilos adicionais se necessário
    return ""


def obter_css_widgets_auto_ajustaveis():
    """
    Retorna CSS para widgets com largura auto-ajustável.

    Returns:
        dict: CSS para cada tipo de widget com largura flexível
    """
    # Como os estilos são aplicados globalmente, retornar dict vazio para compatibilidade
    return {}


def obter_temas_disponiveis():
    """
    Retorna lista de temas disponíveis (Fusion com paletas nativas).

    Returns:
        list: Lista de temas disponíveis
    """
    # Delega ao ThemeManager para evitar duplicação
    try:
        return theme_manager.available_themes()
    except (AttributeError, RuntimeError):
        return ["light", "dark"]


# Funções de conveniência para compatibilidade com código existente
def registrar_tema_actions(actions_dict):
    """Registra as ações de tema para controle de estado no menu."""
    try:
        theme_manager.register_actions(actions_dict)
    except (AttributeError, RuntimeError):
        # Fallback: manter compatibilidade com o gerenciador local
        gerenciador_temas.registrar_tema_actions(actions_dict)


def registrar_cor_actions(actions_dict):
    """Registra ações de menu para cores de destaque (compatibilidade).

    O dicionário deve mapear a chave da cor (ex: 'verde') para um QAction-like.
    """
    try:
        theme_manager.register_color_actions(actions_dict)
    except (AttributeError, RuntimeError):
        # Fallback: apenas ignore se não suportado
        pass


def aplicar_tema_inicial(tema=None):
    """Aplica o tema inicial (delegado ao ThemeManager)."""
    try:
        if tema is None:
            theme_manager.initialize()
        else:
            theme_manager.apply_theme(tema)
    except (AttributeError, RuntimeError):
        gerenciador_temas.aplicar_tema_inicial(tema)


def obter_tema_atual():
    """Retorna o tema atual (delegado ao ThemeManager)."""
    try:
        return theme_manager.current_mode
    except (AttributeError, RuntimeError):
        return gerenciador_temas.obter_tema_atual()


def obter_cores_disponiveis():
    """Retorna as cores de destaque disponíveis (chave -> (rótulo, hex))."""
    try:
        return theme_manager.color_options()
    except (AttributeError, RuntimeError):
        return {}


def obter_estilo_botao(cor: str) -> str:
    """
    Retorna o estilo CSS para botões com a cor especificada.

    Args:
        cor: Uma das cores disponíveis: 'cinza', 'azul', 'amarelo', 'vermelho', 'verde'

    Returns:
        String CSS para aplicar ao botão
    """
    return get_button_style(cor)


def obter_estilo_progress_bar():
    """Retorna o estilo CSS para a barra de progresso."""
    return get_progress_bar_style()


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


def aplicar_estilo_checkbox(checkbox, altura: int = None):
    """Aplica estilo padronizado para checkboxes.

    Args:
        checkbox: O checkbox QCheckBox a ser configurado
        altura: Altura do checkbox (padrão: ALTURA_PADRAO_COMPONENTE)
    """
    if not hasattr(checkbox, "setFixedHeight"):
        return

    altura_final = altura if altura is not None else ALTURA_PADRAO_COMPONENTE
    checkbox.setFixedHeight(altura_final)


def obter_estilo_table_widget():
    """
    Retorna CSS para QTableWidget com aparência de grade visual.

    Returns:
        str: CSS para simular grade em QTableWidget
    """
    return get_table_widget_style()


def aplicar_estilo_table_widget(table_widget):
    """
    Aplica estilo com grade visual ao QTableWidget.

    Args:
        table_widget: O QTableWidget a receber o estilo
    """
    if hasattr(table_widget, "setStyleSheet"):
        table_widget.setStyleSheet(obter_estilo_table_widget())


def get_button_style(color: str) -> str:
    """
    Retorna o estilo CSS para botões com a cor especificada.

    Args:
        color: Uma das cores disponíveis: 'cinza', 'azul', 'amarelo', 'vermelho', 'verde', 'laranja'

    Returns:
        String CSS para aplicar ao botão
    """
    if color not in BUTTON_COLORS:
        color = "cinza"  # fallback para cor padrão

    colors = BUTTON_COLORS[color]
    return f"""
    QPushButton {{
        background-color: {colors['normal']};
        color: {colors['text']};
        border: none;
        padding: 4px 8px;
        font-weight: bold;
        border-radius: 5px;
    }}
    QPushButton:hover {{
        background-color: {colors['hover']};
    }}
    QPushButton:pressed {{
        background-color: {colors['pressed']};
    }}
    """


def get_progress_bar_style() -> str:
    """Retorna o estilo CSS para a barra de progresso."""
    return """
        QProgressBar {
            border: 1px solid palette(dark);
            border-radius: 5px;
            text-align: center;
            height: 10px;
            background-color: palette(base);
            color: palette(text);
        }
        QProgressBar::chunk {
            background-color: palette(highlight);
            border-radius: 5px;
        }
    """


def get_table_widget_style() -> str:
    """
    Retorna CSS para QTableWidget com aparência de grade visual.

    Returns:
        str: CSS para simular grade em QTableWidget
    """
    return """
        QTableWidget {
            color: palette(text);
            font-size: 10pt;
        }
        QTableWidget::item {
            padding: 0px;
        }
        QHeaderView::section {
            padding: 0px;
            color: palette(button-text);
        }
    """


def get_widgets_styles() -> str:
    """Retorna todos os estilos CSS combinados para a aplicação."""
    return f"""
    QComboBox {{
        min-height: 1em;
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING_INTERNO_COMPONENTE};
        font-size: 10pt;
    }}

    QComboBox QAbstractItemView {{
        background-color: palette(base);
        color: palette(text);
    }}

    QLineEdit {{
        background-color: palette(base);
        color: palette(text);
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: 1em;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING_INTERNO_COMPONENTE};
        font-size: 10pt;
    }}
    QLabel {{
        background-color: palette(window);
        color: palette(window-text);
        font-size: 10pt;
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: {ALTURA_PADRAO_COMPONENTE}px;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING_INTERNO_COMPONENTE};

    }}
    QLabel#label_titulo {{
        font-size: 10pt;
        color: palette(window-text);
        padding: 0px 0px;
        min-width: auto;
    }}

    QLabel#label_texto {{
        font-size: 10pt;
        color: palette(window-text);
        padding: 0px 0px;
        min-height: auto;
        max-height: auto;

    }}

    QGroupBox {{
        color: palette(window-text);
        margin-top: 20px; /* espaço para o título */
    }}
    QGroupBox#sem_borda {{
        color: palette(window-text);
        border: none;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 7px;
        padding: 0 3px 0 3px;
        color: palette(window-text);
        background: transparent;
    }}
    QToolTip {{
        background-color: palette(base);
        color: palette(text);
        border: 1px solid palette(dark);
    }}

    QMenuBar {{
        background-color: palette(window);
        color: palette(window-text);
        padding: 5px 0px;
        font-size: 10pt;
        spacing: 1px;
    }}

        QMenu {{
            font-size: 10pt;
    }}

        QMessageBox {{
            background-color: palette(window);
            color: palette(window-text);
        }}

        QMessageBox QLabel {{
            max-height: 99999px;
            min-width: 0;
            padding: 0;
            min-height: 0;
        }}
    """


def get_layout_config() -> dict[str, int]:
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
