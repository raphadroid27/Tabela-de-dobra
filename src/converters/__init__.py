"""Módulo de conversão de arquivos.

Este módulo centraliza toda a lógica de conversão de arquivos entre diferentes formatos
(DWG, DXF, PDF, TIF), separando a lógica de negócio da interface gráfica.
"""

from src.converters.worker import CONVERSION_HANDLERS, ConversionWorker

__all__ = [
    "CONVERSION_HANDLERS",
    "ConversionWorker",
]
