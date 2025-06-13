"""
Funções auxiliares para o aplicativo de cálculo de dobras.
"""

from math import pi
import re
from abc import ABC, abstractmethod
from typing import Tuple, Dict
from src.config import globals as g
from src.models.models import Canal
from src.utils.banco_dados import session


def calcular_k_offset(cabecalho_ui):
    """
    Calcula o fator K com base nos valores de espessura, dedução e raio interno.
    Atualiza o label correspondente com o valor calculado.
    """
    try:
        # Obtém os valores diretamente e verifica se são válidos
        espessura = float(cabecalho_ui.espessura_widget.get() or 0)
        raio_interno = float(cabecalho_ui.raio_interno_widget.get().replace(",", ".") or 0)
        deducao_espec = float(cabecalho_ui.deducao_especifica_widget.get().replace(",", ".") or 0)
        deducao_valor = float(cabecalho_ui.deducao_widget.cget("text") or 0)

        # Usa a dedução específica, se fornecida
        if cabecalho_ui.deducao_especifica_widget.get():
            deducao_valor = deducao_espec

        # Valida se os valores necessários são maiores que zero
        if not raio_interno or not espessura or not deducao_valor:
            return

        # Calcula o fator K
        fator_k = (4 * (espessura - (deducao_valor / 2) + raio_interno) - (pi * raio_interno)) / (
            pi * espessura
        )

        # Limita o fator K a 0.5
        fator_k = min(fator_k, 0.5)

        # Calcula o offset
        offset = fator_k * espessura

        # Atualiza o label com o valor calculado
        cabecalho_ui.fator_k_widget.config(
            text=f"{fator_k:.2f}", fg="blue" if deducao_valor == deducao_espec else "black"
        )

        cabecalho_ui.offset_widget.config(
            text=f"{offset:.2f}", fg="blue" if deducao_valor == deducao_espec else "black"
        )

    except ValueError:
        # Trata erros de conversão
        print("Erro: Valores inválidos fornecidos para o cálculo do fator K.")


def aba_minima_externa(cabecalho_ui):
    """
    Calcula a aba mínima externa com base no valor do canal e na espessura.
    Atualiza o label correspondente com o valor calculado.
    """
    aba_minima_valor = 0  # Valor padrão caso a condição não seja satisfeita

    try:
        if cabecalho_ui.canal_widget.get() != "":
            canal_valor = float(re.findall(r"\d+\.?\d*", cabecalho_ui.canal_widget.get())[0])
            espessura = float(cabecalho_ui.espessura_widget.get())

            aba_minima_valor = canal_valor / 2 + espessura + 2
            cabecalho_ui.aba_minima_widget.config(text=f"{aba_minima_valor:.0f}")
    except (ValueError, AttributeError) as e:
        print(f"Erro ao calcular aba mínima externa: {e}")
        cabecalho_ui.aba_minima_widget.config(text="N/A", fg="red")

    return aba_minima_valor


def z_minimo_externo(cabecalho_ui):
    """
    Calcula o valor mínimo externo com base na espessura, dedução e largura do canal.
    Atualiza o label correspondente com o valor calculado.
    """
    try:
        # Obtém os valores diretamente e verifica se são válidos
        material = cabecalho_ui.material_widget.get()
        espessura = float(cabecalho_ui.espessura_widget.get())
        canal_valor = cabecalho_ui.canal_widget.get()
        deducao_valor = float(cabecalho_ui.deducao_widget.cget("text"))

        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

        if material != "" and espessura != "" and canal_valor != "":
            if not canal_obj.largura:
                cabecalho_ui.z90_widget.config(text="N/A", fg="red")
                return

            if canal_valor and deducao_valor:
                canal_valor = float(re.findall(r"\d+\.?\d*", canal_valor)[0])
                valor_z_min_ext = espessura + (deducao_valor / 2) + (canal_obj.largura / 2) + 2
                cabecalho_ui.z90_widget.config(text=f"{valor_z_min_ext:.0f}", fg="black")

    except ValueError:
        # Trata erros de conversão
        print("Erro: Valores inválidos fornecidos para o cálculo do Z mínimo externo.")


def calcular_dobra(cabecalho_ui, dobras_ui, w):
    """
    Calcula as medidas de dobra e metade de dobra com base nos valores de entrada.
    Versão otimizada usando Strategy Pattern.
    """
    # Obter valores das abas de forma otimizada
    valores_abas = []
    for i in range(1, dobras_ui.n + 1):
        entry = getattr(dobras_ui, f"aba{i}_entry_{w}", None)
        if entry:
            valor = entry.get().replace(",", ".") if entry.get() else ""
            valores_abas.append(valor)
        else:
            valores_abas.append("")

    # Atualizar g.DOBRAS_VALORES de forma mais eficiente
    g.DOBRAS_VALORES = [[valor] for valor in valores_abas]

    # Obter valor da dedução
    deducao_valor = str(cabecalho_ui.deducao_widget.cget("text")).replace(" Copiado!", "")
    deducao_espec = cabecalho_ui.deducao_especifica_widget.get().replace(",", ".")

    # Usar dedução específica se fornecida
    if deducao_espec:
        deducao_valor = deducao_espec

    if not deducao_valor:
        return

    try:
        deducao_float = float(deducao_valor)
    except ValueError:
        print(f"Erro: Valor de dedução inválido: {deducao_valor}")
        return

    # Calcular medidas usando Strategy Pattern
    medidas_calculadas = []

    for i, valor_aba in enumerate(valores_abas, 1):
        if not valor_aba:
            medidas_calculadas.append((0.0, 0.0))
            # Limpar widgets
            getattr(dobras_ui, f"medidadobra{i}_label_{w}").config(text="")
            getattr(dobras_ui, f"metadedobra{i}_label_{w}").config(text="")
        else:
            try:
                dobra_float = float(valor_aba)
                # Determinar se próxima aba está vazia
                proxima_vazia = i < len(valores_abas) and not valores_abas[i]

                # Usar calculador com Strategy Pattern
                medida_dobra, metade_dobra = calculador_dobra.calcular(
                    dobra_float, deducao_float, i, dobras_ui.n, proxima_vazia
                )

                medidas_calculadas.append((medida_dobra, metade_dobra))

                # Atualizar widgets
                getattr(dobras_ui, f"medidadobra{i}_label_{w}").config(
                    text=f"{medida_dobra:.2f}", fg="black"
                )
                getattr(dobras_ui, f"metadedobra{i}_label_{w}").config(
                    text=f"{metade_dobra:.2f}", fg="black"
                )

            except ValueError:
                medidas_calculadas.append((0.0, 0.0))
                print(f"Erro: Valor inválido na aba {i}: {valor_aba}")

        # Verificar aba mínima
        verificar_aba_minima(cabecalho_ui, dobras_ui, valor_aba, i, w)

    # Calcular blank (soma das medidas)
    blank = sum(medida for medida, _ in medidas_calculadas if medida > 0)
    metade_blank = blank / 2 if blank > 0 else 0

    # Atualizar widgets de blank
    blank_label = getattr(dobras_ui, f"medida_blank_label_{w}")
    metade_blank_label = getattr(dobras_ui, f"metade_blank_label_{w}")

    if blank > 0:
        blank_label.config(text=f"{blank:.2f}", fg="black")
        metade_blank_label.config(text=f"{metade_blank:.2f}", fg="black")
    else:
        blank_label.config(text="")
        metade_blank_label.config(text="")


def verificar_aba_minima(cabecalho_ui, dobras_ui, dobra, i, w):
    """
    Verifica se a dobra é menor que a aba mínima e atualiza o widget correspondente.
    """
    # Verificar se a dobra é menor que a aba mínima
    aba_minima = aba_minima_externa(cabecalho_ui)

    # Obter o widget dinamicamente
    entry_widget = getattr(dobras_ui, f"aba{i}_entry_{w}")

    # Verificar se o campo está vazio
    if not dobra.strip():  # Se o campo estiver vazio ou contiver apenas espaços
        entry_widget.config(fg="black", bg="white")
        print(f"Valor vazio na aba {i}, coluna {w}.")
    else:
        try:
            # Converter o valor de 'dobra' para float e verificar se é menor que 'aba_minima'
            if float(dobra) < aba_minima:
                entry_widget.config(fg="white", bg="red")
            else:
                entry_widget.config(fg="black", bg="white")
        except ValueError:
            # Tratar erros de conversão
            entry_widget.config(fg="black", bg="white")
            print(f"Erro: Valor inválido na aba {i}, coluna {w}.")


def razao_ri_espessura(cabecalho_ui, rie_ui):
    """
    Calcula a razão entre o raio interno e a espessura, atualizando o label correspondente.
    """
    if not rie_ui.razao_rie_widget or not rie_ui.razao_rie_widget.winfo_exists():
        return

    try:
        # Obtém os valores diretamente e verifica se são válidos
        espessura = float(cabecalho_ui.espessura_widget.get() or 0)
        raio_interno = float(cabecalho_ui.raio_interno_widget.get().replace(",", ".") or 0)

        # Valida se os valores necessários são maiores que zero
        if not raio_interno or not espessura:
            return

        # Calcula a razão
        razao = raio_interno / espessura

        razao = min(razao, 10)

        # Atualiza o label com o valor calculado
        rie_ui.razao_rie_widget.config(text=f"{razao:.1f}")

    except ValueError:
        # Trata erros de conversão
        print("Erro: Valores inválidos fornecidos para o cálculo da razão.")


# Strategy Pattern para diferentes tipos de cálculo de dobra
class CalculoStrategy(ABC):
    """Interface para estratégias de cálculo de dobra."""

    @abstractmethod
    def calcular_medida_dobra(self, dobra: float, deducao: float, posicao: str) -> float:
        """Calcula a medida da dobra baseado na posição."""
        pass


class CalculoPrimUltAbas(CalculoStrategy):
    """Estratégia para primeira e última abas."""

    def calcular_medida_dobra(self, dobra: float, deducao: float, posicao: str) -> float:
        return dobra - (deducao / 2)


class CalculoAbaMeio(CalculoStrategy):
    """Estratégia para abas do meio."""

    def calcular_medida_dobra(self, dobra: float, deducao: float, posicao: str) -> float:
        return dobra - deducao


class CalculoAbaAdjVazia(CalculoStrategy):
    """Estratégia para aba adjacente a aba vazia."""

    def calcular_medida_dobra(self, dobra: float, deducao: float, posicao: str) -> float:
        return dobra - (deducao / 2)


class CalculadorDobra:
    """Calculador de dobras usando Strategy Pattern."""

    def __init__(self):
        self._strategies: Dict[str, CalculoStrategy] = {
            "primeira_ultima": CalculoPrimUltAbas(),
            "meio": CalculoAbaMeio(),
            "adj_vazia": CalculoAbaAdjVazia(),
        }

    def determinar_estrategia(self, i: int, total_abas: int, proxima_vazia: bool) -> str:
        """Determina qual estratégia usar baseado na posição da aba."""
        if i in (1, total_abas):
            return "primeira_ultima"
        elif proxima_vazia:
            return "adj_vazia"
        else:
            return "meio"

    def calcular(
        self, dobra: float, deducao: float, i: int, total_abas: int, proxima_vazia: bool
    ) -> Tuple[float, float]:
        """
        Calcula medida e metade da dobra.

        Returns:
            Tuple[float, float]: (medida_dobra, metade_dobra)
        """
        if not dobra or dobra == 0:
            return 0.0, 0.0

        estrategia_nome = self.determinar_estrategia(i, total_abas, proxima_vazia)
        estrategia = self._strategies[estrategia_nome]

        medida_dobra = estrategia.calcular_medida_dobra(dobra, deducao, estrategia_nome)
        metade_dobra = medida_dobra / 2

        return medida_dobra, metade_dobra


# Instância global do calculador
calculador_dobra = CalculadorDobra()
