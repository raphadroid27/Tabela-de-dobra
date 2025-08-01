"""
Wrappers de compatibilidade para os formulários universais.
Este arquivo mantém a compatibilidade com o código existente,
redirecionando as chamadas para o formulário universal.

DEPRECATED: Estas classes wrapper são redundantes e podem ser removidas no futuro.
Use diretamente as funções do form_universal.py
"""

from .form_universal import (
    form_deducao_main as main_deducao,
    form_material_main as main_material,
    form_canal_main as main_canal,
    form_espessura_main as main_espessura
)

# Classes wrapper (DEPRECATED - use funções diretas)


class BaseFormWrapper:
    """Classe base para wrappers de formulário - evita repetição de código."""

    @classmethod
    def main(cls, root):
        """Método base que deve ser sobrescrito por subclasses."""
        raise NotImplementedError("Subclasses devem implementar o método main")


class FormDeducao(BaseFormWrapper):
    """Wrapper para o formulário de dedução, mantendo compatibilidade com o código legado."""
    @staticmethod
    def main(root):
        """Inicializa o formulário de dedução universal com o root informado."""
        return main_deducao(root)


class FormMaterial(BaseFormWrapper):
    """Wrapper para o formulário de material, mantendo compatibilidade com o código legado."""
    @staticmethod
    def main(root):
        """Inicializa o formulário de material universal com o root informado."""
        return main_material(root)


class FormCanal(BaseFormWrapper):
    """Wrapper para o formulário de canal, mantendo compatibilidade com o código legado."""
    @staticmethod
    def main(root):
        """Inicializa o formulário de canal universal com o root informado."""
        return main_canal(root)


class FormEspessura(BaseFormWrapper):
    """Wrapper para o formulário de espessura, mantendo compatibilidade com o código legado."""
    @staticmethod
    def main(root):
        """Inicializa o formulário de espessura universal com o root informado."""
        return main_espessura(root)
