"""
Sistema de cache para widgets Tkinter e otimização de loops com getattr().
Reduz custos de reflexão e melhora performance de operações de UI.
"""

from collections import defaultdict
from typing import Any, List


class CacheWidget:
    """Cache inteligente para widgets Tkinter e suas referências."""

    def __init__(self):
        self._refs_widget = defaultdict(dict)  # {object_id: {attr_name: widget}}
        self._listas_widgets = defaultdict(list)  # {pattern: [widgets]}
        self._callbacks_limpeza = []

    def cachear_widget(self, obj: Any, nome_attr: str, widget: Any):
        """
        Armazena referência de widget no cache.

        Args:
            obj: Objeto que contém o widget
            nome_attr: Nome do atributo
            widget: Widget a ser cached
        """
        id_obj = id(obj)
        self._refs_widget[id_obj][nome_attr] = widget

    def obter_widget(self, obj: Any, nome_attr: str, padrao: Any = None) -> Any:
        """
        Recupera widget do cache ou usa getattr como fallback.

        Args:
            obj: Objeto que contém o widget
            nome_attr: Nome do atributo
            padrao: Valor padrão se não encontrado

        Returns:
            Widget ou valor padrão
        """
        id_obj = id(obj)

        # Verificar cache primeiro
        if id_obj in self._refs_widget and nome_attr in self._refs_widget[id_obj]:
            return self._refs_widget[id_obj][nome_attr]

        # Fallback para getattr e armazenar no cache
        widget = getattr(obj, nome_attr, padrao)
        if widget is not padrao:
            self.cachear_widget(obj, nome_attr, widget)

        return widget

    def cachear_lista_widgets(self, padrao: str, widgets: List[Any]):
        """
        Armazena lista de widgets com padrão específico.

        Args:
            padrao: Padrão identificador da lista
            widgets: Lista de widgets
        """
        self._listas_widgets[padrao] = widgets

    def obter_lista_widgets(self, padrao: str) -> List[Any]:
        """
        Recupera lista de widgets por padrão.

        Args:
            padrao: Padrão identificador

        Returns:
            Lista de widgets
        """
        return self._listas_widgets.get(padrao, [])

    def invalidar_objeto(self, obj: Any):
        """Remove todas as referências de um objeto do cache."""
        id_obj = id(obj)
        self._refs_widget.pop(id_obj, None)

    def limpar_cache(self):
        """Limpa todo o cache."""
        self._refs_widget.clear()
        self._listas_widgets.clear()


class OperacoesWidgetOtimizadas:
    """Operações otimizadas para widgets com cache."""

    def __init__(self, cache_widget: CacheWidget):
        self.cache = cache_widget

    def limpar_entradas_otimizado(self, dobras_ui: Any, w: int):
        """
        Versão otimizada de limpeza de entradas usando cache.

        Args:
            dobras_ui: Interface de dobras
            w: Número da coluna
        """
        # Gerar chave para cache de widgets desta operação
        chave_cache = f"entradas_{id(dobras_ui)}_{w}"

        # Tentar recuperar lista cached de widgets
        widgets_em_cache = self.cache.obter_lista_widgets(chave_cache)

        if not widgets_em_cache:
            # Primeira execução - construir cache
            widgets = []
            for i in range(1, dobras_ui.n + 1):  # ✅ Já correto
                entrada = self.cache.obter_widget(dobras_ui, f"aba{i}_entry_{w}")
                if entrada:
                    widgets.append(entrada)

            # Armazenar no cache
            self.cache.cachear_lista_widgets(chave_cache, widgets)
            widgets_em_cache = widgets

        # Usar widgets cached - muito mais rápido que getattr repetitivo
        for entrada in widgets_em_cache:
            if entrada:
                entrada.delete(0, "end")  # Usar 'end' em vez de tk.END para evitar import
                entrada.config(bg="white")

    def limpar_labels_otimizado(self, dobras_ui: Any, w: int):
        """
        Versão otimizada de limpeza de labels usando cache.

        Args:
            dobras_ui: Interface de dobras
            w: Número da coluna
        """
        # Cache para labels de medidas e metades
        chave_cache_labels = f"labels_{id(dobras_ui)}_{w}"
        labels_em_cache = self.cache.obter_lista_widgets(chave_cache_labels)

        if not labels_em_cache:
            # Construir cache de labels
            labels = []
            for i in range(1, dobras_ui.n + 1):  # Corrigido: incluir a última linha
                for prefixo in ["medidadobra", "metadedobra"]:
                    label = self.cache.obter_widget(dobras_ui, f"{prefixo}{i}_label_{w}")
                    if label:
                        labels.append(label)

            # Labels de blank
            for sufixo in ["medida_blank_label", "metade_blank_label"]:
                label = self.cache.obter_widget(dobras_ui, f"{sufixo}_{w}")
                if label:
                    labels.append(label)

            self.cache.cachear_lista_widgets(chave_cache_labels, labels)
            labels_em_cache = labels

        # Limpar usando cache
        for label in labels_em_cache:
            if label:
                label.config(text="")

    def limpar_widgets_cabecalho_otimizado(self, cabecalho_ui: Any):
        """
        Versão otimizada de limpeza de widgets do cabeçalho.

        Args:
            cabecalho_ui: Interface do cabeçalho
        """
        chave_cache = f"widgets_cabecalho_{id(cabecalho_ui)}"
        operacoes_em_cache = self.cache.obter_lista_widgets(chave_cache)

        if not operacoes_em_cache:
            # Construir cache de operações
            operacoes = []

            # Widgets de entrada para limpar
            widgets_entrada = [
                "raio_interno_widget",
                "comprimento_widget",
                "deducao_especifica_widget",
            ]

            for nome_widget in widgets_entrada:
                widget = self.cache.obter_widget(cabecalho_ui, nome_widget)
                if widget:
                    operacoes.append(("limpar_entrada", widget))

            # Widgets de combo para resetar
            widgets_combo = [
                ("material_widget", ""),
                ("espessura_widget", ""),
                ("canal_widget", ""),
            ]

            for nome_widget, valor_padrao in widgets_combo:
                widget = self.cache.obter_widget(cabecalho_ui, nome_widget)
                if widget:
                    operacoes.append(("definir_combo", widget, valor_padrao))

            # Labels para resetar
            widgets_label = [
                ("fator_k_widget", ""),
                ("deducao_widget", ""),
                ("offset_widget", ""),
                ("observacoes_widget", ""),
                ("ton_m_widget", ""),
                ("aba_minima_widget", ""),
                ("z90_widget", ""),
            ]

            for nome_widget, texto in widgets_label:
                widget = self.cache.obter_widget(cabecalho_ui, nome_widget)
                if widget:
                    operacoes.append(("definir_label", widget, texto))

            self.cache.cachear_lista_widgets(chave_cache, operacoes)
            operacoes_em_cache = operacoes

        # Executar operações cached
        for operacao in operacoes_em_cache:
            tipo_op = operacao[0]
            widget = operacao[1]

            if tipo_op == "limpar_entrada":
                widget.delete(0, "end")
            elif tipo_op == "definir_combo":
                valor = operacao[2]
                widget.set(valor)
                if hasattr(widget, "configure"):
                    widget.configure(values=[])
            elif tipo_op == "definir_label":
                texto = operacao[2]
                widget.config(text=texto)


# Instância global do cache de widgets
cache_widget = CacheWidget()
operacoes_otimizadas = OperacoesWidgetOtimizadas(cache_widget)


def cachear_ref_widget(obj: Any, nome_attr: str, widget: Any):
    """Função conveniente para cache de widget."""
    cache_widget.cachear_widget(obj, nome_attr, widget)


def obter_widget_em_cache(obj: Any, nome_attr: str, padrao: Any = None) -> Any:
    """Função conveniente para recuperar widget cached."""
    return cache_widget.obter_widget(obj, nome_attr, padrao)


def limpar_entradas_rapido(dobras_ui: Any, w: int):
    """Função otimizada para limpeza rápida de entradas."""
    operacoes_otimizadas.limpar_entradas_otimizado(dobras_ui, w)


def limpar_labels_rapido(dobras_ui: Any, w: int):
    """Função otimizada para limpeza rápida de labels."""
    operacoes_otimizadas.limpar_labels_otimizado(dobras_ui, w)


def limpar_cabecalho_rapido(cabecalho_ui: Any):
    """Função otimizada para limpeza rápida do cabeçalho."""
    operacoes_otimizadas.limpar_widgets_cabecalho_otimizado(cabecalho_ui)
