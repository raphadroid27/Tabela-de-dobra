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
        self.tema_atual = "light"  # Default
        self.temas_actions = {}
        self.accent_color = QColor(0, 122, 204)  # Azul padrão
        # Registra listener - será feito quando registrar_tema_actions for chamado

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
        return self.tema_atual

    def aplicar_tema_inicial(self, tema=None):
        """
        Aplica o tema inicial na inicialização da aplicação.

        Args:
            tema: Nome do tema inicial (opcional, usa padrão se None)
        """
        if tema is None:
            tema = TEMA_ATUAL_PADRAO

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
    # Fallback: retorna temas padrão
    return ["light", "dark"]


# Funções de conveniência para compatibilidade com código existente
def registrar_tema_actions(actions_dict):
    """Registra as ações de tema para controle de estado no menu."""
    gerenciador_temas.registrar_tema_actions(actions_dict)


def registrar_cor_actions(actions_dict):
    """Registra ações de menu para cores de destaque (compatibilidade).

    O dicionário deve mapear a chave da cor (ex: 'verde') para um QAction-like.
    """
    # Fallback: apenas ignore se não suportado
    _ = actions_dict  # Ignorar parâmetro não utilizado


def aplicar_tema_inicial(tema=None):
    """Aplica o tema inicial (delegado ao ThemeManager)."""
    gerenciador_temas.aplicar_tema_inicial(tema)


def obter_tema_atual():
    """Retorna o tema atual (delegado ao ThemeManager)."""
    return gerenciador_temas.obter_tema_atual()


def obter_cores_disponiveis():
    """Retorna as cores de destaque disponíveis (chave -> (rótulo, hex))."""
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
        min-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING_INTERNO_COMPONENTE};
        font-size: 9pt;
        font-weight: bold;
    }}


    QComboBox QAbstractItemView {{
        background-color: palette(base);
        color: palette(text);
    }}


    QComboBox::item {{
    }}


    QComboBox::item:selected {{
    }}


    QLineEdit {{
        background-color: palette(base);
        color: palette(text);
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: 1em;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING_INTERNO_COMPONENTE};
        font-size: 10pt;
        font-weight: bold
    }}


    QLabel {{
        background-color: palette(window);
        color: palette(window-text);
        font-size: 10pt;
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: {ALTURA_PADRAO_COMPONENTE}px;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING_INTERNO_COMPONENTE};
        font-weight: bold;
    }}


    QLabel#label_titulo {{
        font-size: 10pt;
        color: palette(window-text);
        background-color: transparent;
        padding: 0px 0px;
        min-width: auto;
        font-weight: normal;
    }}


    QLabel#label_titulo_negrito {{
        font-size: 10pt;
        color: palette(window-text);
        padding: 0px 0px;
        min-width: auto;
        font-weight: bold;
    }}


    QLabel#label_texto {{
        font-size: 10pt;
        color: palette(window-text);
        padding: 0px 0px;
        min-height: auto;
        max-height: auto;
        font-weight: normal;
    }}


    QLabel#label_titulo_h4 {{
        font-weight: bold;
        font-size: 16pt;
        color: palette(window-text);
        background-color: transparent;
        min-width: auto;
        min-height: auto;
        margin-top: 0px;
        margin-bottom: 10px;
        padding: 0px 0px;
    }}


    QGroupBox {{
        color: palette(window-text);
        margin-top: 10px; /* espaço para o título */
        font-weight: bold;
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
        background: palette(window);
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


    QMenuBar::item:selected {{
        background-color: palette(highlight);
        color: palette(highlighted-text);
        border-radius: 5px;
    }}


    QMenu {{
        font-size: 10pt;
    }}


    QMenu::item {{
        padding: 5px 10px;
    }}


    QMenu::item:selected {{
        background-color: palette(highlight);
        color: palette(highlighted-text);
        border-radius: 5px;
        margin: 2px 0px;
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
        font-size: 10pt;
        font-weight: normal;
    }}


    QListWidget#lista_categoria {{
        border: none;
        font-size: 10pt;
        background-color: palette(window);
    }}


    QListWidget#lista_categoria::item {{
        color: palette(text);
        border-radius: 5px;
        padding: 4px 8px;
        margin: 3px 0;
    }}


    QListWidget#lista_categoria::item:hover {{
        background-color: palette(base);
        color: palette(text);
    }}


    QListWidget#lista_categoria::item:selected {{
        background-color: palette(highlight);
        color: palette(highlighted-text);
        padding-left: 5px;
        padding-right: 5px;
        border-radius: 6px;
    }}


    QWidget#container_manual {{
        border: none;
        border-radius: 5px;
        background-color: palette(base);
        margin-top: 0px;
    }}


    QTextBrowser {{
        font-size: 10pt;
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
