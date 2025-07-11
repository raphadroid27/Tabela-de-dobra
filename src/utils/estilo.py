"""
Este módulo fornece funções utilitárias para retornar estilos CSS personalizados para
botões do PyQt5 (QPushButton) em diferentes cores temáticas.

Funções disponíveis:
- obter_estilo_botao_cinza(): Retorna o estilo CSS para botões cinza.
- obter_estilo_botao_azul(): Retorna o estilo CSS para botões azuis.
- obter_estilo_botao_amarelo(): Retorna o estilo CSS para botões amarelos.
- obter_estilo_botao_vermelho(): Retorna o estilo CSS para botões vermelhos.
- obter_estilo_botao_verde(): Retorna o estilo CSS para botões verdes.

Cada função retorna uma string contendo o CSS correspondente ao estilo do botão,
incluindo estados de hover e pressed.
"""


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
