# pylint: disable=cyclic-import
"""Gerenciador central de tema usando paletas nativas do PySide6."""

from __future__ import annotations

import ctypes
import sys
from typing import Any, Callable, ClassVar, Dict, List, cast

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

# pylint: disable=too-many-public-methods


class ThemeManager:
    """Aplica e persiste o tema visual da aplicação."""

    # pylint: disable=too-many-instance-attributes

    _INSTANCE: ClassVar["ThemeManager | None"] = None
    _VALID_MODES: ClassVar[set[str]] = {"light", "dark"}
    _SETTINGS_KEY: ClassVar[str] = "appearance/theme_mode"
    _DEFAULT_MODE: ClassVar[str] = "dark"
    _COLOR_SETTINGS_KEY: ClassVar[str] = "appearance/theme_accent"
    _DEFAULT_COLOR: ClassVar[str] = "sistema"
    _STYLE_SETTINGS_KEY: ClassVar[str] = "appearance/theme_style"
    _DEFAULT_STYLE: ClassVar[str] = "Fusion"

    _COLOR_OPTIONS: ClassVar[dict[str, tuple[str, str]]] = {
        "sistema": ("Sistema", "#auto"),  # Cor de destaque do Windows
        "cinza": ("Cinza", "#9E9E9E"),
        "vermelho": ("Vermelho", "#E53935"),
        "laranja": ("Laranja", "#FF5722"),
        "ambar": ("Âmbar", "#FF6F00"),
        "verde": ("Verde", "#4CAF50"),
        "teal": ("Verde-água", "#009688"),
        "ciano": ("Ciano", "#00BCD4"),
        "azul": ("Azul", "#2196F3"),
        "indigo": ("Índigo", "#3F51B5"),
        "roxo": ("Roxo", "#9C27B0"),
        "rosa": ("Rosa", "#EC407A"),
    }

    def __init__(self) -> None:
        """Inicializa o gerenciador de temas."""
        self._settings = None
        # Valores padrão
        self._style = self._DEFAULT_STYLE
        self._mode = self._DEFAULT_MODE
        self._color = self._DEFAULT_COLOR
        self._listeners: List[Callable[[str], None]] = []
        self._color_listeners: List[Callable[[str], None]] = []
        # Dicionário opcional para armazenar ações do menu {cor_key: QAction-like}
        self._color_actions: Dict[str, Any] = {}
        # Dicionário opcional para armazenar ações do menu {tema: QAction-like}
        self._actions: Dict[str, Any] = {}
        # Armazena janelas registradas para aplicar dark title bar
        self._registered_windows: List[QWidget] = []
        # Cache da cor do Windows para detectar mudanças
        self._windows_color_cache: str | None = None

    def _get_settings(self) -> QSettings:
        """Retorna a instância de QSettings, criando se necessário."""
        if self._settings is None:
            self._settings = QSettings()
        return self._settings

    @classmethod
    def instance(cls) -> "ThemeManager":
        """Retorna a instância única do gerenciador de temas."""
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    @property
    def current_mode(self) -> str:
        """Devolve o modo de tema atualmente aplicado."""
        return self._mode

    @property
    def current_color(self) -> str:
        """Retorna a cor de destaque atualmente aplicada."""
        return self._color

    @property
    def current_style(self) -> str:
        """Retorna o estilo atualmente aplicado."""
        return self._style

    def initialize(self) -> None:
        """Aplica o tema salvo sem sobrescrever a preferência."""
        # Carrega os valores salvos
        saved_style = self._get_settings().value(
            self._STYLE_SETTINGS_KEY, self._DEFAULT_STYLE
        )
        if not isinstance(saved_style, str):
            saved_style = self._DEFAULT_STYLE
        self._style = saved_style
        # Garante que seja salvo
        self._get_settings().setValue(self._STYLE_SETTINGS_KEY, self._style)
        self._get_settings().sync()
        QApplication.setStyle(self._style)
        saved_mode = self._get_settings().value(self._SETTINGS_KEY, self._DEFAULT_MODE)
        self._mode = (
            saved_mode
            if isinstance(saved_mode, str) and saved_mode in self._VALID_MODES
            else self._DEFAULT_MODE
        )
        saved_color = self._get_settings().value(
            self._COLOR_SETTINGS_KEY, self._DEFAULT_COLOR
        )
        if not isinstance(saved_color, str) or saved_color not in self._COLOR_OPTIONS:
            saved_color = self._DEFAULT_COLOR
        self._color = saved_color
        self._apply_theme(self._mode, persist=False)

    def apply_theme(self, mode: str) -> None:
        """Aplica o tema desejado e salva a escolha do usuário."""
        self._apply_theme(mode, persist=True)

    def apply_color(self, color_key: str) -> None:
        """Aplica uma nova cor de destaque para o tema."""
        if color_key not in self._COLOR_OPTIONS:
            return
        if color_key == self._color:
            return
        self._color = color_key
        self._get_settings().setValue(self._COLOR_SETTINGS_KEY, color_key)
        self._get_settings().sync()
        self._apply_theme(self._mode, persist=False)
        self._notify_color_listeners()

    def apply_style(self, style: str) -> None:
        """Aplica um novo estilo para a aplicação."""
        if style == self._style:
            return
        self._style = style
        self._get_settings().setValue(self._STYLE_SETTINGS_KEY, style)
        self._get_settings().sync()
        QApplication.setStyle(style)
        # Força atualização de todos os widgets para aplicar o novo estilo
        for widget in QApplication.allWidgets():
            widget.repaint()

    def refresh_interface(self) -> None:
        """Força atualização completa da interface.

        Reaplica o tema atual, verifica mudanças na cor do Windows (se aplicável)
        e força repaint de todos os widgets. Útil para corrigir problemas visuais
        ou atualizar após mudanças externas no sistema.
        """
        self._apply_theme(self._mode, persist=False)

    def register_listener(self, callback: Callable[[str], None]) -> None:
        """Registra um callback para ser notificado quando o tema mudar."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str], None]) -> None:
        """Remove um callback previamente registrado."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def register_color_listener(self, callback: Callable[[str], None]) -> None:
        """Registra um callback para notificações de mudança de cor de destaque."""
        if callback not in self._color_listeners:
            self._color_listeners.append(callback)

    def unregister_color_listener(self, callback: Callable[[str], None]) -> None:
        """Remove um callback previamente registrado para mudanças de cor."""
        if callback in self._color_listeners:
            self._color_listeners.remove(callback)

    def register_color_actions(self, actions: Dict[str, Any]) -> None:
        """Registra ações de menu para as cores de destaque.

        O dicionário deve mapear a chave da cor (ex: 'verde') para um objeto tipo
        QAction que suporte `setChecked(bool)`. Será chamado `_update_color_actions`
        para sincronizar o estado inicial.
        """
        self._color_actions = dict(actions)
        self._update_color_actions()

    def unregister_color_actions(self) -> None:
        """Remove o registro de actions de cor."""
        self._color_actions = {}

    def _update_color_actions(self) -> None:
        """Marca/desmarca as actions de cor conforme `_color` atual."""
        actions = getattr(self, "_color_actions", None)
        if not actions:
            return
        for cor_key, action in actions.items():
            try:
                if hasattr(action, "setChecked"):
                    action.setChecked(cor_key == self._color)
            except (AttributeError, RuntimeError, TypeError):
                # Não deixar erro externo quebrar a aplicação do tema
                continue

    def _create_light_palette(self, accent_color: QColor) -> QPalette:
        """Cria uma paleta clara nativa com cor de destaque."""
        palette = QPalette()
        # Cores para tema claro
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, accent_color)
        palette.setColor(QPalette.ColorRole.Highlight, accent_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(0, 0, 0, 128))
        return palette

    def _create_dark_palette(self, accent_color: QColor) -> QPalette:
        """Cria uma paleta escura nativa com cor de destaque."""
        palette = QPalette()
        # Cores para tema escuro
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, accent_color)
        palette.setColor(QPalette.ColorRole.Highlight, accent_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(255, 255, 255, 128))
        return palette

    def _apply_theme(self, mode: str, *, persist: bool) -> None:
        selected = mode if mode in self._VALID_MODES else self._DEFAULT_MODE

        # Atualiza o modo ANTES de aplicar qualquer mudança visual
        self._mode = selected
        if persist:
            self._get_settings().setValue(self._SETTINGS_KEY, selected)
            self._get_settings().sync()

        # Verificar se a cor do Windows mudou (apenas se "sistema" estiver ativo)
        if self._color == "sistema":
            current_windows_color = self._get_windows_accent_color()
            # Inicializa cache na primeira vez
            if self._windows_color_cache is None:
                self._windows_color_cache = current_windows_color
            # Notifica mudança se a cor for diferente
            elif self._windows_color_cache != current_windows_color:
                self._windows_color_cache = current_windows_color
                self._notify_color_listeners()

        app = QApplication.instance()
        accent_color = QColor(self._get_accent_hex())
        if app is not None:
            app = cast(QApplication, app)
            if selected == "dark":
                palette = self._create_dark_palette(accent_color)
            else:
                palette = self._create_light_palette(accent_color)
            app.setPalette(palette)

            # Aplicar estilos CSS globais que usam palette()
            # Import local para evitar import circular
            # pylint: disable=import-outside-toplevel
            from .estilo import get_widgets_styles

            global_styles = get_widgets_styles(selected)
            app.setStyleSheet(global_styles)

            # Força atualização de todos os widgets para aplicar a nova paleta
            for widget in QApplication.allWidgets():
                widget.repaint()

        # Atualiza a barra de título de todas as janelas registradas
        # Usa QTimer para garantir que a atualização aconteça após o repaint
        # Delay de 50ms para garantir que todas as atualizações visuais completaram
        QTimer.singleShot(50, self._update_all_title_bars)

        for callback in list(self._listeners):
            callback(selected)

        # Atualiza actions de menu, se houver (ignora erros específicos)
        try:
            self._update_actions()
            self._update_color_actions()
        except (AttributeError, RuntimeError, TypeError):
            pass

    @classmethod
    def color_options(cls) -> dict[str, tuple[str, str]]:
        """Retorna mapa de cores disponíveis (chave -> (rótulo, hex))."""
        return dict(cls._COLOR_OPTIONS)

    def available_themes(self) -> List[str]:
        """Retorna lista de temas disponíveis (modo visual)."""
        return list(self._VALID_MODES)

    def register_actions(self, actions: Dict[str, Any]) -> None:
        """Registra um dicionário {tema: QAction-like} para sincronizar checks.

        O objeto associado a cada tema apenas precisa expor `setChecked(bool)`.
        """
        self._actions = dict(actions)
        self._update_actions()

    def unregister_actions(self) -> None:
        """Remove o dicionário de actions registrado."""
        self._actions = {}

    def _update_actions(self) -> None:
        """Marca/desmarca os QAction registrados conforme o tema atual."""
        actions = getattr(self, "_actions", None)
        if not actions:
            return
        # Primeiro, garantir que todos fiquem desmarcados
        for action in actions.values():
            try:
                if hasattr(action, "setChecked"):
                    action.setChecked(False)
            except (AttributeError, RuntimeError, TypeError):
                continue

        # Em seguida, marcar apenas a action correspondente ao tema atual
        active = self._mode
        action = actions.get(active)
        if action and hasattr(action, "setChecked"):
            try:
                action.setChecked(True)
            except (AttributeError, RuntimeError, TypeError):
                pass

    def _get_accent_hex(self) -> str:
        """Obtém a cor hexadecimal da cor de destaque atual.

        Se a cor for 'sistema', obtém a cor de destaque do Windows.
        """
        if self._color == "sistema":
            return self._get_windows_accent_color()

        rotulo_hex = self._COLOR_OPTIONS.get(
            self._color, self._COLOR_OPTIONS[self._DEFAULT_COLOR]
        )
        return rotulo_hex[1]

    @staticmethod
    def _get_windows_accent_color() -> str:
        """Obtém a cor de destaque do Windows via registro.

        Returns:
            Cor hexadecimal no formato '#RRGGBB'
        """
        try:
            # Tentar obter via winreg (mais confiável)
            import winreg  # pylint: disable=import-outside-toplevel

            key_path = r"Software\Microsoft\Windows\DWM"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
            value, _ = winreg.QueryValueEx(key, "AccentColor")
            winreg.CloseKey(key)

            # Converter DWORD para RGB (formato: 0xAABBGGRR)
            r = value & 0xFF
            g = (value >> 8) & 0xFF
            b = (value >> 16) & 0xFF

            return f"#{r:02X}{g:02X}{b:02X}"
        except (ImportError, OSError, ValueError):
            # Fallback para azul se não conseguir obter a cor do Windows
            return "#2196F3"

    def _notify_color_listeners(self) -> None:
        for callback in list(self._color_listeners):
            callback(self._color)

    def register_window(self, window: QWidget) -> None:
        """Registra uma janela para aplicar dark title bar automaticamente.

        Args:
            window: Janela (QMainWindow, QDialog, etc.) para aplicar dark title bar
        """
        if window not in self._registered_windows:
            self._registered_windows.append(window)
            # Aplica imediatamente se o tema atual for dark
            if self._mode == "dark":
                self._apply_dark_title_bar(window)

    def unregister_window(self, window: QWidget) -> None:
        """Remove uma janela da lista de janelas registradas.

        Args:
            window: Janela a ser removida
        """
        if window in self._registered_windows:
            self._registered_windows.remove(window)

    def _apply_dark_title_bar(self, window: QWidget) -> None:
        """Aplica barra de título dark mode no Windows.

        Args:
            window: Janela para aplicar o dark mode na barra de título
        """
        if sys.platform != "win32":
            return

        try:
            hwnd = int(window.winId())

            # Constantes do Windows DWM API
            # Windows 11 / Windows 10 20H1+
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # pylint: disable=invalid-name
            # Windows 10 versões antigas (build 18985-19041)
            DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19  # pylint: disable=invalid-name

            # 1 = dark mode, 0 = light mode
            value = ctypes.c_int(1 if self._mode == "dark" else 0)

            # Tenta API mais recente, depois fallback para versões antigas
            for attr in (
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                DWMWA_USE_IMMERSIVE_DARK_MODE_OLD,
            ):
                try:
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
                    )
                    break  # Sucesso, não precisa tentar o fallback
                except Exception:  # pylint: disable=broad-except
                    continue  # Tenta próxima versão da API

            # Força atualização da janela para aplicar a mudança
            try:
                # SetWindowPos com SWP_FRAMECHANGED força o redraw da moldura
                # Flags: 0x0020=FRAMECHANGED | 0x0002=NOMOVE | 0x0001=NOSIZE
                #        0x0004=NOZORDER | 0x0010=NOACTIVATE
                flags = 0x0020 | 0x0002 | 0x0001 | 0x0004 | 0x0010
                ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, flags)
            except Exception:  # pylint: disable=broad-except
                window.repaint()

        except Exception:  # pylint: disable=broad-except
            # Não deixar erro na API do Windows quebrar a aplicação
            pass

    def _update_all_title_bars(self) -> None:
        """Atualiza a barra de título de todas as janelas registradas."""
        for window in list(self._registered_windows):
            try:
                self._apply_dark_title_bar(window)
            except (AttributeError, RuntimeError):
                # Janela pode ter sido destruída
                self._registered_windows.remove(window)


# Instância global
# pylint: disable=C0103
theme_manager = ThemeManager.instance()
