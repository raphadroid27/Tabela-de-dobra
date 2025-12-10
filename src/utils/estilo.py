# pylint: disable=cyclic-import
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

TEMA_ATUAL_PADRAO = "dark"

# Constantes de layout e estilo
ALTURA_PADRAO_COMPONENTE = 20
LARGURA_MINIMA_COMPONENTE = 70
PADDING_INTERNO_COMPONENTE = "2px 4px"
ALTURA_PADRAO_BOTAO = 25
LARGURA_MINIMA_BOTAO = 20
ALTURA_PADRAO_MENU = 18

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


# Funções de conveniência para compatibilidade com código existente
def registrar_tema_actions(actions_dict):
    """Registra as ações de tema para controle de estado no menu."""
    gerenciador_temas.registrar_tema_actions(actions_dict)


def aplicar_tema_inicial(tema=None):
    """Aplica o tema inicial (delegado ao ThemeManager)."""
    gerenciador_temas.aplicar_tema_inicial(tema)


def obter_tema_atual():
    """Retorna o tema atual (delegado ao ThemeManager)."""
    return gerenciador_temas.obter_tema_atual()


def obter_estilo_botao(cor: str) -> str:
    """
    Retorna o estilo CSS para botões com a cor especificada.

    Args:
        cor: Uma das cores disponíveis: 'cinza', 'azul', 'amarelo', 'vermelho', 'verde'

    Returns:
        String CSS para aplicar ao botão
    """
    return _get_button_style(cor)


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
    return _get_table_widget_style()


def aplicar_estilo_table_widget(table_widget):
    """
    Aplica estilo com grade visual ao QTableWidget.

    Args:
        table_widget: O QTableWidget a receber o estilo
    """
    if hasattr(table_widget, "setStyleSheet"):
        table_widget.setStyleSheet(obter_estilo_table_widget())


# Estilos individuais para widgets


def _get_button_style(color: str) -> str:
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


def _get_progress_bar_style(theme: str = "light") -> str:
    """Retorna o estilo CSS para a barra de progresso.

    Args:
        theme: Tema atual ('light' ou 'dark') para determinar cor da borda
    """
    # Define cor da borda - mesma lógica do QComboBox e QLineEdit
    border_color = "#B6B6B6" if theme == "light" else "#242424"

    return f"""
        QProgressBar {{
            border: 1px solid {border_color};
            border-radius: 5px;
            text-align: center;
            height: {ALTURA_PADRAO_BOTAO}px;
            background-color: palette(base);
            color: palette(text);
            font-size: 10pt;
        }}

        QProgressBar::chunk {{
            background-color: palette(highlight);
            border-radius: 4px;
        }}
    """


def _get_table_widget_style() -> str:
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


def _get_combo_box_style(theme: str = "light") -> str:
    """Retorna CSS para QComboBox.

    Args:
        theme: Tema atual ('light' ou 'dark') para determinar cor da seta
    """
    # pylint: disable=import-outside-toplevel
    from src.utils.utilitarios import obter_caminho_svg

    # Seleciona a seta apropriada baseada no tema
    arrow_file = (
        obter_caminho_svg("arrow_down_white.svg")
        if theme == "dark"
        else obter_caminho_svg("arrow_down.svg")
    ).replace(
        "\\", "/"
    )  # Converte para barras normais no CSS
    # Define cor da borda
    border_color = "#B6B6B6" if theme == "light" else "#242424"

    return f"""
    QComboBox {{
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING_INTERNO_COMPONENTE};
        font-size: 9pt;
        font-weight: bold;
        border: 1px solid {border_color};
        border-radius: none;
        background-color: palette(base);
        color: palette(text);
    }}

    QComboBox::drop-down {{
        border: none;
        background-color: transparent;
    }}

    QComboBox::down-arrow {{
        image: url("{arrow_file}");
        width: 10px;
        height: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: palette(base);
        color: palette(text);
        border: none;
        selection-background-color: palette(highlight);
        selection-color: palette(highlighted-text);
    }}

    QComboBox::item {{
        min-height: {ALTURA_PADRAO_MENU}px;
        max-height: {ALTURA_PADRAO_MENU}px;
        padding: 5px 10px 5px -20px;
    }}

    QComboBox::item:selected {{
        background-color: palette(highlight);
        color: palette(highlighted-text);
        border-radius: 5px;
        margin: 2px 0px;
    }}

    QComboBox:hover {{
        border: 1px solid palette(highlight);
    }}
    """


def _get_line_edit_style(theme: str = "light") -> str:
    """Retorna CSS para QLineEdit.

    Args:
        theme: Tema atual ('light' ou 'dark') para determinar cor da borda
    """
    # Define cor da borda
    border_color = "#B6B6B6" if theme == "light" else "#242424"

    return f"""
    QLineEdit {{
        background-color: palette(base);
        color: palette(text);
        min-width: {LARGURA_MINIMA_COMPONENTE}px;
        min-height: {ALTURA_PADRAO_COMPONENTE}px;
        max-height: {ALTURA_PADRAO_COMPONENTE}px;
        padding: {PADDING_INTERNO_COMPONENTE};
        font-size: 10pt;
        font-weight: bold;
        border: 1px solid {border_color};
        border-radius: none;
    }}

    QLineEdit:hover {{
        border: 1px solid palette(highlight);
    }}

    QLineEdit:focus {{
        border: 1px solid palette(highlight);
    }}
    """


def _get_label_style() -> str:
    """Retorna CSS para QLabel e suas variações (label_titulo, label_texto, etc)."""
    return f"""
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
    """


def _get_group_box_style() -> str:
    """Retorna CSS para QGroupBox."""
    return """
    QGroupBox {
        color: palette(window-text);
        margin-top: 10px; /* espaço para o título */
        font-weight: bold;
    }

    QGroupBox#sem_borda {
        color: palette(window-text);
        border: none;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 7px;
        padding: 0 3px 0 3px;
        color: palette(window-text);
        background: palette(window);
    }
    """


def _get_tooltip_style() -> str:
    """Retorna CSS para QToolTip."""
    return """
    QToolTip {
        background-color: palette(base);
        color: palette(text);
        border: 1px solid palette(dark);
        font-size: 10pt;
    }
    """


def _get_menu_bar_style() -> str:
    """Retorna CSS para QMenuBar."""
    return """
    QMenuBar {
        background-color: palette(window);
        color: palette(window-text);
        padding: 5px 0px;
        font-size: 10pt;
        spacing: 1px;
        min-height: {ALTURA_PADRAO_MENU}px;
        max-height: {ALTURA_PADRAO_MENU}px;
    }

    QMenuBar::item:selected {
        background-color: palette(highlight);
        color: palette(highlighted-text);
        border-radius: 5px;
    }
    """


def _get_menu_style(check_icon: str) -> str:
    """Retorna CSS para QMenu e seus indicadores."""
    return f"""
    QMenu {{
        background-color: palette(base);
        border: none;
        font-size: 10pt;
    }}

    QMenu::item {{
        min-height: {ALTURA_PADRAO_MENU}px;
        max-height: {ALTURA_PADRAO_MENU}px;
        padding: 5px 10px;
    }}

    QMenu::item:selected {{
        background-color: palette(highlight);
        color: palette(highlighted-text);
        border-radius: 5px;
        margin: 2px 0px;
    }}

    QMenu::indicator:non-exclusive {{
        width: 12px;
        height: 12px;
        margin-left: 6px;
        border-radius: 3px;
    }}

    QMenu::indicator:non-exclusive:unchecked {{
        border: 1px solid #595959;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 palette(button),
                                    stop:1 palette(base));
    }}

    QMenu::indicator:non-exclusive:hover {{
        border: 1px solid palette(highlight);
    }}

    QMenu::indicator:non-exclusive:checked {{
        border: 1px solid #595959;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 palette(button),
                                    stop:1 palette(base));
        background-image: url("{check_icon}");
        background-repeat: no-repeat;
        background-position: center;
    }}

    QMenu::indicator:non-exclusive:hover {{
        border: 1px solid palette(highlight);
        background-color: palette(midlight);
    }}
    """


def _get_checkbox_style(check_icon: str) -> str:
    """Retorna CSS para QCheckBox e seus indicadores."""
    return f"""
    QCheckBox {{
        spacing: 8px;
        font-size: 10pt;
        font-weight: normal;
    }}

    QCheckBox::indicator {{
        width: 12px;
        height: 12px;
        margin-left: 6px;
        border-radius: 3px;
    }}

    QCheckBox::indicator:unchecked {{
        border: 1px solid #595959;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 palette(button),
                                    stop:1 palette(base));
    }}

    QCheckBox::indicator:unchecked:hover,
    QCheckBox::indicator:checked:hover {{
        border: 1px solid palette(highlight);
    }}

    QCheckBox::indicator:checked {{
        border: 1px solid #595959;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 palette(button),
                                    stop:1 palette(base));
        background-image: url("{check_icon}");
        background-repeat: no-repeat;
        background-position: center;
    }}

    QCheckBox::indicator:checked:disabled,
    QCheckBox::indicator:unchecked:disabled {{
        border: 1px solid #595959;
        background-color: palette(midlight);
    }}
    """


def _get_message_box_style() -> str:
    """Retorna CSS para QMessageBox."""
    return """
    QMessageBox {
        background-color: palette(window);
        color: palette(window-text);
    }

    QMessageBox QLabel {
        max-height: 99999px;
        min-width: 0;
        padding: 0;
        min-height: 0;
        font-size: 10pt;
        font-weight: normal;
    }
    """


def _get_list_widget_style() -> str:
    """Retorna CSS para QListWidget (lista_categoria)."""
    return """
    QListWidget#lista_categoria {
        border: none;
        font-size: 10pt;
        background-color: palette(window);
    }

    QListWidget#lista_categoria::item {
        color: palette(text);
        border-radius: 5px;
        padding: 4px 8px;
        margin: 3px 0;
    }

    QListWidget#lista_categoria::item:hover {
        background-color: palette(base);
        color: palette(text);
    }

    QListWidget#lista_categoria::item:selected {
        background-color: palette(highlight);
        color: palette(highlighted-text);
        padding-left: 5px;
        padding-right: 5px;
        border-radius: 6px;
    }
    """


def _get_container_manual_style() -> str:
    """Retorna CSS para QWidget (container_manual)."""
    return """
    QWidget#container_manual {
        border: none;
        border-radius: 5px;
        background-color: palette(base);
        margin-top: 0px;
    }
    """


def _get_text_browser_style() -> str:
    """Retorna CSS para QTextBrowser."""
    return """
    QTextBrowser {
        font-size: 10pt;
    }
    """


def get_widgets_styles(theme: str = "light") -> str:
    """Retorna todos os estilos CSS combinados para a aplicação.

    Combina os estilos de todos os widgets chamando as funções individuais
    para cada tipo de widget.
    """
    # pylint: disable=import-outside-toplevel
    from src.utils.utilitarios import obter_caminho_svg

    tema_normalizado = (theme or "light").lower()
    check_icon = obter_caminho_svg("check.svg").replace("\\", "/")
    if tema_normalizado == "dark":
        check_icon = obter_caminho_svg("check_white.svg").replace("\\", "/")

    return f"""
    {_get_combo_box_style(tema_normalizado)}
    {_get_line_edit_style(tema_normalizado)}
    {_get_label_style()}
    {_get_group_box_style()}
    {_get_tooltip_style()}
    {_get_menu_bar_style()}
    {_get_menu_style(check_icon)}
    {_get_checkbox_style(check_icon)}
    {_get_message_box_style()}
    {_get_list_widget_style()}
    {_get_container_manual_style()}
    {_get_text_browser_style()}
    {_get_progress_bar_style(tema_normalizado)}
    """
