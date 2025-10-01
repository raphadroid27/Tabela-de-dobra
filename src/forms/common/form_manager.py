"""Gerenciadores utilitários para formulários com instância única."""

from __future__ import annotations

from typing import Optional, Type

from PySide6.QtWidgets import QWidget


class BaseSingletonFormManager:
    """Gerencia instâncias únicas de formulários Qt."""

    FORM_CLASS: Optional[Type[QWidget]] = None
    _instance: Optional[QWidget] = None

    @classmethod
    def _reset_instance(cls) -> None:
        """Limpa a referência interna quando a janela é destruída."""
        cls._instance = None

    @classmethod
    def show_form(cls, parent: QWidget | None = None) -> None:
        """Mostra a janela gerenciada, reutilizando a instância existente."""
        if cls.FORM_CLASS is None:
            raise RuntimeError("FORM_CLASS não configurada no gerenciador.")

        if cls._instance is None or not cls._instance.isVisible():
            if cls._instance:
                cls._instance.deleteLater()
            cls._instance = cls.FORM_CLASS(parent)
            cls._instance.destroyed.connect(cls._reset_instance)
            cls._instance.show()
        else:
            cls._instance.activateWindow()
            cls._instance.raise_()
