"""Utilitários para resolver expressões simples em QLineEdit de forma segura."""

import ast
import operator as op
import re
from typing import Optional

from PySide6.QtWidgets import QLineEdit

_OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv}


def _resolver_no_ast(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_resolver_no_ast(node.operand)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](
            _resolver_no_ast(node.left), _resolver_no_ast(node.right)
        )
    raise ValueError("Operacao nao permitida")


def _formatar_decimal(valor: float) -> str:
    texto = f"{valor:.4f}".rstrip("0").rstrip(".")
    texto = texto or "0"
    return texto.replace(".", ",")


def avaliar_expressao_para_texto(expr: str) -> Optional[str]:
    """Avalia expressão simples e devolve texto formatado com vírgula."""
    if not expr:
        return None

    sanitized = expr.replace(" ", "").replace(",", ".")
    if not any(op_char in sanitized for op_char in ["+", "-", "*", "/", "(", ")"]):
        return None
    if not re.fullmatch(r"[0-9.+\-*/()]*", sanitized):
        return None

    try:
        node = ast.parse(sanitized, mode="eval").body
        valor = _resolver_no_ast(node)
        return _formatar_decimal(valor)
    except (SyntaxError, ValueError, TypeError):
        return None


def resolver_expressao_no_line_edit(entry: QLineEdit) -> None:
    """Substitui o texto do QLineEdit pelo resultado, se a expressão for válida."""
    if entry is None:
        return
    texto_atual = entry.text()
    resultado = avaliar_expressao_para_texto(texto_atual)
    if resultado is None:
        return

    pos = entry.cursorPosition()
    entry.blockSignals(True)
    entry.setText(resultado)
    entry.setCursorPosition(min(pos, len(resultado)))
    entry.blockSignals(False)
