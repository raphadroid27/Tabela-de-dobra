"""Compatibilidade para importações legadas de workers de conversão.

Historicamente, este módulo continha uma cópia da implementação principal
em ``src.forms.converter_worker``. Para evitar manutenção duplicada e os
avisos de código repetido do pylint, o módulo agora apenas reexporta as
entidades públicas originais.
"""

from __future__ import annotations

from src.forms.converter_worker import CONVERSION_HANDLERS, ConversionWorker

__all__ = ["CONVERSION_HANDLERS", "ConversionWorker"]
