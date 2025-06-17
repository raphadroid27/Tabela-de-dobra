"""
Este módulo contém funções auxiliares para o aplicativo de cálculo de dobras.

As funções incluem a atualização de widgets, manipulação de valores de dobras,
restauração de valores, e outras operações relacionadas ao funcionamento do
aplicativo de cálculo de dobras.
"""

import tkinter as tk
from tkinter import ttk
import re
from typing import cast

import pyperclip

from src.utils.banco_dados import session, obter_configuracoes
from src.utils.cache import (
    obter_materiais_em_cache,
    obter_espessuras_em_cache,
    obter_canais_em_cache,
    cache_manager,
)
from src.utils.calculos import (
    calcular_dobra,
    calcular_k_offset,
    aba_minima_externa,
    z_minimo_externo,
    razao_ri_espessura,
)
from src.config import globals as g
import src.utils.classes.dica_ferramenta as tp


def atualizar_rie_se_aberta(cabecalho_ui):
    """
    Verifica se a janela de razão R/E está aberta e atualiza o valor se necessário.
    """
    try:
        # Importar aqui para evitar importação circular
        from src.forms.form_razao_rie import FormRIE  # pylint: disable=import-outside-toplevel

        # Verificação simplificada da instância ativa
        instancia = FormRIE.instancia_ativa

        # Verificar se a instância existe e a janela ainda está ativa
        if (
            instancia
            and hasattr(instancia, "rie_form")
            and instancia.rie_form
            and instancia.rie_form.winfo_exists()
        ):
            # Chamar a função de cálculo da razão
            razao_ri_espessura(cabecalho_ui, instancia)

    except (AttributeError, ImportError, TypeError):
        # Se houver erro de importação circular ou atributo, simplesmente ignora
        pass


def atualizar_widgets(cabecalho_ui, form_ui, tipo):
    """
    Atualiza os valores de comboboxes com base no tipo especificado.

    Args:
        cabecalho_ui: Interface do cabeçalho
        deducao_ui: Interface de dedução (pode ser None)
        tipo (str): O tipo de combobox a ser atualizado.
    """

    def atualizar_material():
        if (
            cabecalho_ui
            and cabecalho_ui.material_widget
            and cabecalho_ui.material_widget.winfo_exists()
        ):
            materiais = [m.nome for m in obter_materiais_em_cache()]
            cabecalho_ui.material_widget.configure(values=materiais)

        # Verifica se o combobox de dedução de material existe e atualiza seus valores
        if (
            form_ui
            and hasattr(form_ui, "deducao_material_combo")
            and form_ui.deducao_material_combo
            and form_ui.deducao_material_combo.winfo_exists()
        ):
            form_ui.deducao_material_combo.configure(
                values=[m.nome for m in obter_materiais_em_cache()]
            )

    def atualizar_espessura():
        material_nome = cabecalho_ui.material_widget.get()
        # Usar cache para buscar material
        materiais = obter_materiais_em_cache()
        material_obj = next((m for m in materiais if m.nome == material_nome), None)

        if material_obj:
            # Buscar espessuras relacionadas usando cache
            espessuras = obter_espessuras_em_cache()
            # Filtrar espessuras válidas para o material através das deduções
            deducoes = cache_manager.get_cached_data("deducoes")
            espessuras_validas = [
                e
                for e in espessuras
                if any(
                    d.material_id == material_obj.id and d.espessura_id == e.id
                    for d in deducoes
                )
            ]
            # Ordenar espessuras por valor numérico (converter para evitar problemas de tipagem)
            def get_valor_numerico(espessura):
                """Extrai o valor numérico da espessura para ordenação."""
                try:
                    # Usar getattr para obter o valor atual do atributo
                    valor = getattr(espessura, 'valor', 0)
                    return float(valor) if valor is not None else 0.0
                except (ValueError, TypeError, AttributeError):
                    return 0.0

            espessuras_validas.sort(key=get_valor_numerico)
            cabecalho_ui.espessura_widget.configure(
                values=[str(e.valor) for e in espessuras_validas]
            )

        # Verifica se o combobox de dedução de espessura existe e atualiza seus valores
        if (
            form_ui
            and hasattr(form_ui, "deducao_espessura_combo")
            and form_ui.deducao_espessura_combo
            and form_ui.deducao_espessura_combo.winfo_exists()        ):
            # Extrair valores numéricos das espessuras para ordenação
            espessuras_valores = []
            for e in obter_espessuras_em_cache():
                try:
                    valor = getattr(e, 'valor', 0)
                    if valor is not None:
                        espessuras_valores.append(float(valor))
                except (ValueError, TypeError, AttributeError):
                    continue

            form_ui.deducao_espessura_combo.configure(
                values=sorted(espessuras_valores)
            )

    def atualizar_canal():
        espessura_valor = cabecalho_ui.espessura_widget.get()
        material_nome = cabecalho_ui.material_widget.get()        # Usar cache para buscar objetos
        espessuras = obter_espessuras_em_cache()
        materiais = obter_materiais_em_cache()

        espessura_obj = None
        if espessura_valor:
            try:
                valor_buscado = float(espessura_valor)
                for e in espessuras:
                    # Comparar valores de forma segura, evitando ColumnElement
                    try:
                        valor_espessura = float(getattr(e, 'valor', 0))
                        # Comparação com tolerância para valores de ponto flutuante
                        if abs(valor_espessura - valor_buscado) < 0.001:
                            espessura_obj = e
                            break
                    except (ValueError, TypeError, AttributeError):
                        continue
            except (ValueError, TypeError):
                espessura_obj = None

        material_obj = None
        for m in materiais:
            try:
                nome_material = getattr(m, 'nome', '')
                if nome_material == material_nome:
                    material_obj = m
                    break
            except (AttributeError, TypeError):
                continue

        if espessura_obj and material_obj:
            # Buscar canais relacionados usando cache
            canais = obter_canais_em_cache()
            deducoes = cache_manager.get_cached_data("deducoes")

            # Filtrar canais válidos para o material e espessura
            canais_validos = [
                c
                for c in canais
                if any(
                    d.material_id == material_obj.id
                    and d.espessura_id == espessura_obj.id
                    and d.canal_id == c.id
                    for d in deducoes
                )
            ]

            canais_valores = sorted(
                [str(c.valor) for c in canais_validos],
                key=lambda x: float(re.findall(r"\d+\.?\d*", x)[0]),
            )
            cabecalho_ui.canal_widget.configure(values=canais_valores)

        # Verifica se o combobox de dedução de canal existe e atualiza seus valores
        if (
            form_ui
            and hasattr(form_ui, "deducao_canal_combo")
            and form_ui.deducao_canal_combo
            and form_ui.deducao_canal_combo.winfo_exists()        ):
            # Extrair valores dos canais para ordenação
            canais_valores = []
            for c in obter_canais_em_cache():
                try:
                    valor = getattr(c, 'valor', '')
                    if valor is not None:
                        canais_valores.append(str(valor))
                except (ValueError, TypeError, AttributeError):
                    continue

            form_ui.deducao_canal_combo.configure(
                values=sorted(canais_valores)
            )

    def atualizar_deducao():
        espessura_valor = cabecalho_ui.espessura_widget.get()
        material_nome = cabecalho_ui.material_widget.get()
        canal_valor = cabecalho_ui.canal_widget.get()        # Usar cache para buscar objetos
        espessuras = obter_espessuras_em_cache()
        materiais = obter_materiais_em_cache()
        canais = obter_canais_em_cache()

        espessura_obj = None
        if espessura_valor:
            try:
                valor_buscado = float(espessura_valor)
                for e in espessuras:
                    try:
                        valor_espessura = float(getattr(e, 'valor', 0))
                        if abs(valor_espessura - valor_buscado) < 0.001:
                            espessura_obj = e
                            break
                    except (ValueError, TypeError, AttributeError):
                        continue
            except (ValueError, TypeError):
                espessura_obj = None

        material_obj = None
        for m in materiais:
            try:
                nome_material = getattr(m, 'nome', '')
                if nome_material == material_nome:
                    material_obj = m
                    break
            except (AttributeError, TypeError):
                continue

        canal_obj = None
        for c in canais:
            try:
                valor_canal = getattr(c, 'valor', '')
                if valor_canal == canal_valor:
                    canal_obj = c
                    break
            except (AttributeError, TypeError):
                continue

        if espessura_obj and material_obj and canal_obj:
            # Buscar dedução usando cache
            deducoes = cache_manager.get_cached_data("deducoes")
            # Buscar dedução de forma segura, evitando ColumnElement comparisons
            deducao_obj = None
            try:
                espessura_id = int(getattr(espessura_obj, 'id', 0))
                material_id = int(getattr(material_obj, 'id', 0))
                canal_id = int(getattr(canal_obj, 'id', 0))

                for d in deducoes:
                    try:
                        d_espessura_id = int(getattr(d, 'espessura_id', 0))
                        d_material_id = int(getattr(d, 'material_id', 0))
                        d_canal_id = int(getattr(d, 'canal_id', 0))

                        if (d_espessura_id == espessura_id and
                            d_material_id == material_id and
                            d_canal_id == canal_id):
                            deducao_obj = d
                            break
                    except (ValueError, TypeError, AttributeError):
                        continue
            except (ValueError, TypeError, AttributeError):
                deducao_obj = None

            if deducao_obj:
                cabecalho_ui.deducao_widget.config(text=deducao_obj.valor, fg="black")
                observacao = deducao_obj.observacao or "Observações não encontradas"
                cabecalho_ui.observacoes_widget.config(text=f"{observacao}")
            else:
                cabecalho_ui.deducao_widget.config(text="N/A", fg="red")
                cabecalho_ui.observacoes_widget.config(text="Observações não encontradas")

    # Mapeamento de tipos para funções
    acoes = {
        "material": atualizar_material,
        "espessura": atualizar_espessura,
        "canal": atualizar_canal,
        "dedução": atualizar_deducao,
    }

    # Executa a ação correspondente ao tipo
    if tipo in acoes:
        acoes[tipo]()


def canal_tooltip(cabecalho_ui):
    """
    Atualiza o tooltip do combobox de canais com as
    observações e comprimento total do canal selecionado.
    """
    if cabecalho_ui.canal_widget.get() == "":
        cabecalho_ui.canal_widget.set("")
        tp.DicaFerramenta(cabecalho_ui.canal_widget, "Selecione o canal de dobra.")
    else:        # Usar cache para buscar canal
        canais = obter_canais_em_cache()
        canal_obj = next((c for c in canais if c.valor == cabecalho_ui.canal_widget.get()), None)

        if canal_obj:
            # Extrair valores de forma segura, evitando problemas com Column[str] e Column[Unknown]
            try:
                canal_obs_valor = getattr(canal_obj, 'observacao', None)
                canal_obs = str(canal_obs_valor) if canal_obs_valor is not None else "N/A."
            except (AttributeError, TypeError):
                canal_obs = "N/A."

            try:
                canal_comprimento_valor = getattr(canal_obj, 'comprimento_total', None)
                canal_comprimento_total = (
                    str(canal_comprimento_valor)
                    if canal_comprimento_valor is not None
                    else "N/A."
                )
            except (AttributeError, TypeError):
                canal_comprimento_total = "N/A."

            tp.DicaFerramenta(
                cabecalho_ui.canal_widget,
                f"Obs: {canal_obs}\n" f"Comprimento total: {canal_comprimento_total}",
                delay=0,
            )


def atualizar_toneladas_m(cabecalho_ui):
    """
    Atualiza o valor de toneladas por metro com base no comprimento e na dedução selecionada.
    """
    comprimento = cabecalho_ui.comprimento_widget.get()
    espessura_valor = cabecalho_ui.espessura_widget.get()
    material_nome = cabecalho_ui.material_widget.get()
    canal_valor = cabecalho_ui.canal_widget.get()

    # Usar cache para buscar objetos (elimina consultas duplicadas)
    espessuras = obter_espessuras_em_cache()
    materiais = obter_materiais_em_cache()
    canais = obter_canais_em_cache()

    espessura_obj = None
    if espessura_valor:
        try:
            valor_buscado = float(espessura_valor)
            for e in espessuras:
                try:
                    valor_espessura = float(getattr(e, 'valor', 0))
                    if abs(valor_espessura - valor_buscado) < 0.001:
                        espessura_obj = e
                        break
                except (ValueError, TypeError, AttributeError):
                    continue
        except (ValueError, TypeError):
            espessura_obj = None

    material_obj = None
    for m in materiais:
        try:
            nome_material = getattr(m, 'nome', '')
            if nome_material == material_nome:
                material_obj = m
                break
        except (AttributeError, TypeError):
            continue

    canal_obj = None
    for c in canais:
        try:
            valor_canal = getattr(c, 'valor', '')
            if valor_canal == canal_valor:
                canal_obj = c
                break
        except (AttributeError, TypeError):
            continue

    if espessura_obj and material_obj and canal_obj:
        # Usar cache para buscar dedução - extrair IDs de forma segura
        try:
            material_id = int(getattr(material_obj, 'id', 0))
            espessura_id = int(getattr(espessura_obj, 'id', 0))
            canal_id = int(getattr(canal_obj, 'id', 0))
            deducao_obj = cache_manager.get_deducao(material_id, espessura_id, canal_id)
        except (ValueError, TypeError, AttributeError):
            deducao_obj = None

        if deducao_obj and deducao_obj.forca is not None:
            toneladas_m = (
                (deducao_obj.forca * float(comprimento)) / 1000
                if comprimento
                else deducao_obj.forca
            )
            cabecalho_ui.ton_m_widget.config(text=f"{toneladas_m:.0f}", fg="black")
        else:
            cabecalho_ui.ton_m_widget.config(text="N/A", fg="red")

    # Verificar comprimento usando objeto já consultado (elimina consulta duplicada)
    comprimento_total = None
    if canal_obj:
        try:
            comprimento_total_valor = getattr(canal_obj, 'comprimento_total', None)
            comprimento_total = (
                float(comprimento_total_valor)
                if comprimento_total_valor is not None
                else None
            )
        except (ValueError, TypeError, AttributeError):
            comprimento_total = None

    comprimento_float = None
    if comprimento:
        try:
            comprimento_float = float(comprimento)
        except (ValueError, TypeError):
            comprimento_float = None

    if canal_obj and comprimento_float and comprimento_total:
        if comprimento_float < comprimento_total:
            cabecalho_ui.comprimento_widget.config(fg="black")
        elif comprimento_float >= comprimento_total:
            cabecalho_ui.comprimento_widget.config(fg="red")


def restaurar_valores_dobra(dobras_ui, w):
    """
    Restaura os valores das dobras para a coluna específica w
    a partir de g.DOBRAS_VALORES.
    """
    # Verificar se g.DOBRAS_VALORES foi inicializada
    if not hasattr(g, "DOBRAS_VALORES") or g.DOBRAS_VALORES is None:
        print("DOBRAS_VALORES não foi inicializada ou está vazia")
        return

    try:
        # Restaurar os valores das dobras apenas para a coluna w
        for i in range(1, dobras_ui.n + 1):  # ✅ CORRIGIDO: incluir a última linha
            # Verificar se existem dados para esta linha e coluna
            if i - 1 < len(g.DOBRAS_VALORES) and w - 1 < len(g.DOBRAS_VALORES[i - 1]):
                valor = g.DOBRAS_VALORES[i - 1][w - 1]
                entry = getattr(dobras_ui, f"aba{i}_entry_{w}", None)
                if entry and hasattr(entry, "winfo_exists") and entry.winfo_exists():
                    entry.delete(0, tk.END)
                    entry.insert(0, valor)
                    print(f"Valor restaurado para aba{i}_entry_{w}: {valor}")
                else:
                    print(f"Widget aba{i}_entry_{w} não existe ou foi destruído")
            else:
                print(f"Não há dados salvos para aba{i}_entry_{w}")

    except (AttributeError, IndexError, ValueError, TypeError) as e:
        print(f"Erro ao restaurar valores das dobras: {e}")


def salvar_valores_cabecalho(cabecalho_ui):
    """
    Salva os valores atuais dos widgets no cabeçalho em g.CABECALHO_VALORES.
    """
    if not hasattr(g, "CABECALHO_VALORES") or not isinstance(g.CABECALHO_VALORES, dict):
        g.CABECALHO_VALORES = {}

    try:
        g.CABECALHO_VALORES = {
            "material": (
                cabecalho_ui.material_widget.get()
                if hasattr(cabecalho_ui, "material_widget") and cabecalho_ui.material_widget
                else ""
            ),
            "espessura": (
                cabecalho_ui.espessura_widget.get()
                if hasattr(cabecalho_ui, "espessura_widget") and cabecalho_ui.espessura_widget
                else ""
            ),
            "canal": (
                cabecalho_ui.canal_widget.get()
                if hasattr(cabecalho_ui, "canal_widget") and cabecalho_ui.canal_widget
                else ""
            ),
            "comprimento": (
                cabecalho_ui.comprimento_widget.get()
                if hasattr(cabecalho_ui, "comprimento_widget") and cabecalho_ui.comprimento_widget
                else ""
            ),
            "raio_interno": (
                cabecalho_ui.raio_interno_widget.get()
                if hasattr(cabecalho_ui, "raio_interno_widget") and cabecalho_ui.raio_interno_widget
                else ""
            ),
            "deducao_especifica": (
                cabecalho_ui.deducao_especifica_widget.get()
                if hasattr(cabecalho_ui, "deducao_especifica_widget")
                and cabecalho_ui.deducao_especifica_widget
                else ""
            ),
        }
        print("Valores salvos:", g.CABECALHO_VALORES)

    except (AttributeError, TypeError) as e:
        print(f"Erro ao salvar valores do cabeçalho: {e}")
        g.CABECALHO_VALORES = {}


def restaurar_valores_cabecalho(cabecalho_ui):
    """
    Restaura os valores dos widgets no cabeçalho
    com base nos valores armazenados em g.CABECALHO_VALORES.
    """    # Verifica se g.CABECALHO_VALORES já foi inicializado como um dicionário
    if not hasattr(g, "CABECALHO_VALORES") or not isinstance(g.CABECALHO_VALORES, dict):
        g.CABECALHO_VALORES = {}
        return

    try:
        # Garantir que temos um dicionário válido antes de iterar
        cabecalho_valores = cast(dict, g.CABECALHO_VALORES)
        if not cabecalho_valores:
            print("Nenhum valor salvo para restaurar.")
            return

        # Restaura os valores nos widgets
        for widget_name, valor in cabecalho_valores.items():
            if hasattr(cabecalho_ui, f"{widget_name}_widget"):
                widget = getattr(cabecalho_ui, f"{widget_name}_widget")
                if widget and hasattr(widget, "winfo_exists") and widget.winfo_exists():
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                        widget.insert(0, valor)
                    elif isinstance(widget, ttk.Combobox):
                        widget.set(valor)
                    print(f"Valor restaurado para {widget_name}: {valor}")
                else:
                    print(f"Widget {widget_name}_widget não existe ou foi destruído")
            else:
                print(f"Atributo {widget_name}_widget não encontrado em cabecalho_ui")

        print("Valores restaurados:", g.CABECALHO_VALORES)
    except (AttributeError, KeyError, ValueError) as e:
        print(f"Erro ao restaurar valores do cabeçalho: {e}")


def copiar(dobras_ui, cabecalho_ui, tipo, numero=None, w=None):
    """
    Copia o valor do label correspondente ao tipo e
    número especificados para a área de transferência.
    """
    configuracoes = {
        "dedução": {
            "label": cabecalho_ui.deducao_widget,
            "funcao_calculo": lambda: (
                atualizar_widgets(cabecalho_ui, None, "dedução"),
                calcular_k_offset(cabecalho_ui),
            ),
        },
        "fator_k": {
            "label": cabecalho_ui.fator_k_widget,
            "funcao_calculo": lambda: (
                atualizar_widgets(cabecalho_ui, None, "dedução"),
                calcular_k_offset(cabecalho_ui),
            ),
        },
        "offset": {
            "label": cabecalho_ui.offset_widget,
            "funcao_calculo": lambda: (
                atualizar_widgets(cabecalho_ui, None, "dedução"),
                calcular_k_offset(cabecalho_ui),
            ),
        },
        "medida_dobra": {
            "label": lambda numero: getattr(dobras_ui, f"medidadobra{numero}_label_{w}", None),
            "funcao_calculo": lambda: calcular_dobra(cabecalho_ui, dobras_ui, w),
        },
        "metade_dobra": {
            "label": lambda numero: getattr(dobras_ui, f"metadedobra{numero}_label_{w}", None),
            "funcao_calculo": lambda: calcular_dobra(cabecalho_ui, dobras_ui, w),
        },
        "blank": {
            "label": getattr(dobras_ui, f"medida_blank_label_{w}", None),
            "funcao_calculo": lambda: calcular_dobra(cabecalho_ui, dobras_ui, w),
        },
        "metade_blank": {
            "label": getattr(dobras_ui, f"metade_blank_label_{w}", None),
            "funcao_calculo": lambda: calcular_dobra(cabecalho_ui, dobras_ui, w),        },
    }

    config = configuracoes.get(tipo)
    if not config:
        print(f"Tipo '{tipo}' não encontrado nas configurações.")
        return

    label = config["label"](numero) if callable(config["label"]) else config["label"]

    if label is None:
        print(f"Erro: Label não encontrado para o tipo '{tipo}' com numero={numero} e w={w}.")
        return

    # Verificar se o label é um widget válido do tkinter
    if not hasattr(label, "cget") or not hasattr(label, "config"):
        print(f"Erro: O objeto para o tipo '{tipo}' não é um widget válido do tkinter.")
        return

    try:
        # Fazer cast para tk.Label para resolver problemas de tipagem
        widget_label = cast(tk.Label, label)

        # Verificar se o texto está vazio
        texto_atual = str(widget_label.cget("text"))
        if texto_atual == "":
            return

        # Executar cálculo e copiar
        config["funcao_calculo"]()
        texto_atual = str(widget_label.cget("text"))
        pyperclip.copy(texto_atual)
        print(f'Valor copiado {texto_atual}')
        widget_label.config(text=f'{texto_atual} Copiado!', fg="green")
    except tk.TclError as e:
        print(f"Erro ao acessar widget para o tipo '{tipo}': {e}")
    except (ValueError, AttributeError, OSError) as e:
        print(f"Erro inesperado ao copiar valor do tipo '{tipo}': {e}")


def limpar_dobras(cabecalho_ui, dobras_ui, app_principal):
    """
    Limpa os valores das dobras e atualiza os labels correspondentes.
    """

    def limpar_widgets(widgets, metodo, valor=""):
        """
        Limpa ou redefine widgets com base no método fornecido.

        Args:
            widgets (list): Lista de widgets a serem limpos.
            metodo (str): Método a ser chamado no widget (ex.: 'delete', 'config').
            valor (str): Valor a ser usado no método (se aplicável).
        """
        for widget in widgets:
            if widget:
                if metodo == "delete":
                    getattr(widget, metodo)(0, tk.END)
                else:
                    widget.config(text=valor)

    # Obter widgets dinamicamente
    def obter_widgets(prefixo):
        return [
            getattr(dobras_ui, f"{prefixo}{i}_label_{col}", None)
            for i in range(1, dobras_ui.n)
            for col in app_principal.valores_w
        ]

    # Limpar entradas e labels
    dobras = [
        getattr(dobras_ui, f"aba{i}_entry_{col}", None)
        for i in range(1, dobras_ui.n)
        for col in app_principal.valores_w
    ]
    medidas = obter_widgets("medidadobra")
    metades = obter_widgets("metadedobra")
    blanks = [
        getattr(dobras_ui, f"medida_blank_label_{col}", None) for col in app_principal.valores_w
    ]
    metades_blanks = [
        getattr(dobras_ui, f"metade_blank_label_{col}", None) for col in app_principal.valores_w
    ]

    # Limpar widgets
    limpar_widgets(dobras, "delete")
    limpar_widgets(medidas + metades + blanks + metades_blanks, "config", "")

    # Limpar dedução específica
    if cabecalho_ui.deducao_especifica_widget:
        cabecalho_ui.deducao_especifica_widget.delete(0, tk.END)

    # Resetar valores globais
    g.DOBRAS_VALORES = []

    # Alterar a cor de fundo das entradas de dobras para branco
    for i in range(1, dobras_ui.n):
        for col in app_principal.valores_w:
            entry = getattr(dobras_ui, f"aba{i}_entry_{col}", None)
            if entry:
                entry.config(bg="white")

    # Verifique se o atributo existe antes de usá-lo
    aba1_entry = getattr(dobras_ui, "aba1_entry_1", None)
    if aba1_entry:
        aba1_entry.focus_set()


def limpar_tudo(cabecalho_ui, dobras_ui, app_principal):
    """
    Limpa todos os campos e labels do aplicativo.
    """
    try:
        # Limpar campos do cabeçalho usando a instância cabecalho_ui
        if hasattr(cabecalho_ui, "material_widget") and cabecalho_ui.material_widget:
            cabecalho_ui.material_widget.set("")
        if hasattr(cabecalho_ui, "espessura_widget") and cabecalho_ui.espessura_widget:
            cabecalho_ui.espessura_widget.set("")
            cabecalho_ui.espessura_widget.configure(values=[])
        if hasattr(cabecalho_ui, "canal_widget") and cabecalho_ui.canal_widget:
            cabecalho_ui.canal_widget.set("")
            cabecalho_ui.canal_widget.configure(values=[])

        # Limpar entradas
        if hasattr(cabecalho_ui, "raio_interno_widget") and cabecalho_ui.raio_interno_widget:
            cabecalho_ui.raio_interno_widget.delete(0, tk.END)
        if hasattr(cabecalho_ui, "comprimento_widget") and cabecalho_ui.comprimento_widget:
            cabecalho_ui.comprimento_widget.delete(0, tk.END)
        if (
            hasattr(cabecalho_ui, "deducao_especifica_widget")
            and cabecalho_ui.deducao_especifica_widget
        ):
            cabecalho_ui.deducao_especifica_widget.delete(0, tk.END)

        # Limpar etiquetas
        etiquetas_widgets = [
            ("fator_k_widget", ""),
            ("deducao_widget", ""),
            ("offset_widget", ""),
            ("observacoes_widget", ""),
            ("ton_m_widget", ""),
            ("aba_minima_widget", ""),
            ("z90_widget", ""),
        ]

        for widget_name, texto in etiquetas_widgets:
            if hasattr(cabecalho_ui, widget_name):
                widget = getattr(cabecalho_ui, widget_name)
                if widget:
                    widget.config(text=texto)

        # Limpar dobras
        limpar_dobras(cabecalho_ui, dobras_ui, app_principal)

        # Executar todas as funções
        todas_funcoes(cabecalho_ui, dobras_ui)

        # Limpar razão R/E se existir
        if hasattr(g, "RAZAO_RIE_LBL") and g.RAZAO_RIE_LBL and g.RAZAO_RIE_LBL.winfo_exists():
            g.RAZAO_RIE_LBL.config(text="")

        # Focar no combobox de material
        if hasattr(cabecalho_ui, "material_widget") and cabecalho_ui.material_widget:
            cabecalho_ui.material_widget.focus_set()

    except (AttributeError, tk.TclError) as e:
        print(f"Erro ao limpar todos os campos: {e}")


def limpar_busca(tipo, form_ui):
    """
    Limpa os campos de busca e atualiza a lista correspondente.
    """
    configuracoes = obter_configuracoes(form_ui)
    config = configuracoes.get(tipo)

    if not config:
        return

    if tipo == "dedução":
        if "entries" in config:
            config["entries"]["material_combo"].delete(0, tk.END)
            config["entries"]["espessura_combo"].delete(0, tk.END)
            config["entries"]["canal_combo"].delete(0, tk.END)
    else:
        if "busca" in config and config["busca"]:
            config["busca"].delete(0, tk.END)

    listar(tipo, form_ui)


def focus_next_entry(current_index, w, dobras_ui):
    """
    Move o foco para o próximo campo de entrada na aba atual.
    """
    next_index = current_index + 1
    if next_index <= dobras_ui.n:
        next_entry = getattr(dobras_ui, f"aba{next_index}_entry_{w}", None)
        if next_entry:
            next_entry.focus()


def focus_previous_entry(current_index, w, dobras_ui):
    """
    Move o foco para o campo de entrada anterior na aba atual.
    """
    previous_index = current_index - 1
    if previous_index > 0:
        previous_entry = getattr(dobras_ui, f"aba{previous_index}_entry_{w}", None)
        if previous_entry:
            previous_entry.focus()


def listar(tipo, ui):
    """
    Lista os itens do banco de dados na interface gráfica.
    """
    configuracoes = obter_configuracoes(ui)
    config = configuracoes.get(tipo)

    if not config or not config["lista"] or not config["lista"].winfo_exists():
        return

    for item in config["lista"].get_children():
        config["lista"].delete(item)

    itens = session.query(config["modelo"]).order_by(config["ordem"]).all()

    if tipo == "material":
        itens = sorted(itens, key=lambda x: x.nome)

    for item in itens:
        if tipo == "dedução":
            if item.material is None or item.espessura is None or item.canal is None:
                continue
        config["lista"].insert("", "end", values=config["valores"](item))


def todas_funcoes(
    cabecalho_ui, dobras_ui=None, todas_colunas=False, app_principal=None
):
    """
    Executa todas as funções necessárias para atualizar os valores e labels do aplicativo.    Args:
        cabecalho_ui: Interface do cabeçalho
        dobras_ui: Interface de dobras específica (opcional)
        todas_colunas: Se True, recalcula todas as colunas ativas
        app_principal: Instância do app para acessar todas as colunas
    """
    for tipo in ["material", "espessura", "canal", "dedução"]:
        atualizar_widgets(cabecalho_ui, None, tipo)

    atualizar_toneladas_m(cabecalho_ui)
    calcular_k_offset(cabecalho_ui)
    aba_minima_externa(cabecalho_ui)
    z_minimo_externo(cabecalho_ui)

    # Se deve recalcular todas as colunas e tem app_principal
    if todas_colunas and app_principal and hasattr(app_principal, "dobras_ui"):
        for w in app_principal.valores_w:
            if w in app_principal.dobras_ui:
                calcular_dobra(cabecalho_ui, app_principal.dobras_ui[w], w)
    elif dobras_ui:
        # Calcular dobra apenas para a coluna específica passada como parâmetro
        if hasattr(dobras_ui, "w"):
            w = dobras_ui.w
            calcular_dobra(cabecalho_ui, dobras_ui, w)

    # Verificar se existe janela de razão R/E aberta e atualizar se necessário
    atualizar_rie_se_aberta(cabecalho_ui)

    # Atualizar tooltips
    canal_tooltip(cabecalho_ui)


def configurar_main_frame(parent, rows=4):
    """
    Configura o frame principal com colunas e linhas padrão.
    """
    main_frame = tk.Frame(parent)
    main_frame.pack(pady=5, padx=5, fill="both", expand=True)

    main_frame.columnconfigure(0, weight=1)
    for i in range(rows):
        main_frame.rowconfigure(i, weight=1 if i == 1 else 0)

    return main_frame


def configurar_frame_edicoes(parent, text, columns=3, rows=4):
    """
    Cria um frame de edições com configuração padrão.
    """
    frame_edicoes = tk.LabelFrame(parent, text=text, pady=5)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    for i in range(columns):
        frame_edicoes.columnconfigure(i, weight=1 if i < columns - 1 else 0)

    for i in range(rows):
        frame_edicoes.rowconfigure(i, weight=1)

    return frame_edicoes


def salvar_valores_dobra(dobras_ui, w):
    """
    Salva os valores atuais das dobras da coluna específica w em g.DOBRAS_VALORES.
    """
    try:
        if not hasattr(g, "DOBRAS_VALORES") or g.DOBRAS_VALORES is None:
            g.DOBRAS_VALORES = []

        # Garantir que g.DOBRAS_VALORES tenha o tamanho necessário para as linhas
        while (
            len(g.DOBRAS_VALORES) < dobras_ui.n
        ):  # ✅ Corrigido: dobras_ui.n em vez de dobras_ui.n - 1
            g.DOBRAS_VALORES.append([])

        # Salvar os valores das dobras apenas para a coluna w
        for i in range(1, dobras_ui.n + 1):  # ✅ Corrigido: incluir a última linha
            # Garantir que cada linha tenha o tamanho necessário para conter até a coluna w
            while len(g.DOBRAS_VALORES[i - 1]) < w:
                g.DOBRAS_VALORES[i - 1].append("")

            # Salvar apenas a coluna específica w
            entry = getattr(dobras_ui, f"aba{i}_entry_{w}", None)
            if entry and hasattr(entry, "winfo_exists") and entry.winfo_exists():
                valor = entry.get()
                g.DOBRAS_VALORES[i - 1][w - 1] = valor
                print(f"Valor salvo para aba{i}_entry_{w}: {valor}")
            else:
                g.DOBRAS_VALORES[i - 1][w - 1] = ""

        print(f"Valores de dobras salvos para coluna {w}:", g.DOBRAS_VALORES)
    except (KeyError, IndexError, ValueError, AttributeError) as e:
        print(f"Erro ao salvar valores das dobras: {e}")
