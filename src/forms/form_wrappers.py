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
    @staticmethod
    def main(root):
        return main_deducao(root)

# Classe wrapper para form_material  
class form_material:
    @staticmethod
    def main(root):
        return main_material(root)

# Classe wrapper para form_canal
class form_canal:
    @staticmethod
    def main(root):
        return main_canal(root)

# Classe wrapper para form_espessura
class form_espessura:
    @staticmethod
    def main(root):
        return main_espessura(root)
