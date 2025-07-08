"""
Wrappers de compatibilidade para os formulários universais.
Este arquivo mantém a compatibilidade com o código existente,
redirecionando as chamadas para o formulário universal.
"""

from .form_universal import (
    form_deducao_main as main_deducao,
    form_material_main as main_material,
    form_canal_main as main_canal,
    form_espessura_main as main_espessura
)

# Classe wrapper para form_deducao


class form_deducao:
    """Wrapper para o formulário de dedução, mantendo compatibilidade com o código legado."""
    @staticmethod
    def main(root):
        """Inicializa o formulário de dedução universal com o root informado."""
        return main_deducao(root)

# Classe wrapper para form_material


class form_material:
    """Wrapper para o formulário de material, mantendo compatibilidade com o código legado."""
    @staticmethod
    def main(root):
        """Inicializa o formulário de material universal com o root informado."""
        return main_material(root)

# Classe wrapper para form_canal


class form_canal:
    """Wrapper para o formulário de canal, mantendo compatibilidade com o código legado."""
    @staticmethod
    def main(root):
        """Inicializa o formulário de canal universal com o root informado."""
        return main_canal(root)

# Classe wrapper para form_espessura


class form_espessura:
    """Wrapper para o formulário de espessura, mantendo compatibilidade com o código legado."""
    @staticmethod
    def main(root):
        """Inicializa o formulário de espessura universal com o root informado."""
        return main_espessura(root)
