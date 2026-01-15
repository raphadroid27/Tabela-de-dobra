"""
Módulo de Interface para o Aplicativo de Dobras.

Este módulo contém funções que interagem diretamente com a interface gráfica
(widgets PySide6). Ele é responsável por:
- Orquestrar os cálculos do módulo `calculos`.
- Ler os dados da UI, chamar a lógica de cálculo e atualizar os widgets com os resultados.
- Gerenciar a aparência (estilos, tooltips) dos widgets.
- Lidar com ações diretas na interface, como limpeza de campos e cópia de valores.
"""

import logging
import traceback
import os  # Adicionado para acesso à imagem de assets
from dataclasses import dataclass
from functools import partial
from typing import Any, Dict, Optional

import pyperclip
from PySide6.QtCore import QTimer
from sqlalchemy.exc import SQLAlchemyError

from src.config import globals as g
from src.models.models import Canal, Deducao, Espessura, Material, Usuario
from src.utils import calculos
from src.utils.banco_dados import get_session
from src.utils.cache_manager import cache_manager
from src.utils.widget import WidgetManager, append_row

# pylint: disable=R0902


@dataclass
class UIData:
    """Estrutura para armazenar os dados coletados da interface."""

    material_nome: str
    espessura_str: str
    canal_str: str
    raio_interno_str: str
    comprimento_str: str
    deducao_espec_str: str
    espessura: float
    raio_interno: float
    comprimento: float
    deducao_espec: float
    deducao_usada: float = 0.0


class CopyManager:
    """Gerencia operações de cópia de valores dos widgets."""

    def __init__(self):
        """Inicializa o gerenciador de operações de cópia."""
        self.configuracoes = {
            "dedução": {"label": lambda *_: g.DED_LBL},
            "fator_k": {"label": lambda *_: g.K_LBL},
            "offset": {"label": lambda *_: g.OFFSET_LBL},
            "medida_dobra": {
                "label": lambda n, w: getattr(g, f"medidadobra{n}_label_{w}", None)
            },
            "metade_dobra": {
                "label": lambda n, w: getattr(g, f"metadedobra{n}_label_{w}", None)
            },
            "blank": {
                "label": lambda _, w: getattr(g, f"medida_blank_label_{w}", None)
            },
            "metade_blank": {
                "label": lambda _, w: getattr(g, f"metade_blank_label_{w}", None)
            },
        }

    def copiar(self, tipo, numero=None, w=None):
        """Copia o valor do label para a área de transferência."""
        if not self.configuracoes:
            return
        label_func = self.configuracoes.get(tipo, {}).get("label")
        if not label_func:
            return
        label = label_func(numero, w)
        if not WidgetManager.is_widget_valid(label):
            return

        calcular_valores()
        texto_original = label.text().replace(" Copiado!", "")
        if not texto_original.strip():
            return

        pyperclip.copy(texto_original)
        label.setText("Copiado!")
        label.setStyleSheet("QLabel { color: green; }")
        QTimer.singleShot(500, partial(self._restaurar_label, label, texto_original))

    def _restaurar_label(self, label, texto):
        """Restaura o texto e estilo original do label."""
        if not WidgetManager.is_widget_valid(label):
            return

        data = _coletar_dados_entrada()
        estilo = _estilo(data)
        if "Copiado!" in label.text():
            label.setText(texto)
            label.setStyleSheet(estilo)


copiar = CopyManager().copiar


class ListManager:
    """Gerencia operações de listagem de dados do banco na interface."""

    def __init__(self):
        self.configuracoes: Optional[Dict[str, Dict[str, Any]]] = None

    def listar(self, tipo):
        """Lista os itens do banco de dados na interface gráfica."""
        self.configuracoes = obter_configuracoes()
        if not self.configuracoes or tipo not in self.configuracoes:
            return

        config = self.configuracoes[tipo]
        table_widget = config.get("lista")
        if not table_widget:
            return

        table_widget.setRowCount(0)
        try:
            with get_session() as session:
                if tipo == "dedução":
                    itens = (
                        session.query(config["modelo"])
                        .join(Material)
                        .join(Espessura)
                        .join(Canal)
                        .order_by(config["ordem"])
                        .all()
                    )
                else:
                    itens = (
                        session.query(config["modelo"]).order_by(config["ordem"]).all()
                    )

                for item in itens:
                    valores = config["valores"](item)
                    if valores is None:
                        continue
                    append_row(table_widget, valores)
        except SQLAlchemyError as e:
            logging.error("Erro ao listar itens do tipo '%s': %s", tipo, e)


listar = ListManager().listar


class LimparBusca:
    """Classe para limpar campos de busca dos formulários."""

    def limpar_busca(self, tipo):
        """Limpa os campos de busca e atualiza a lista correspondente."""
        try:
            configuracoes = obter_configuracoes()
            if tipo not in configuracoes:
                return
            config = configuracoes[tipo]
            if tipo == "dedução":
                self._limpar_busca_deducao(config)
            else:
                self._limpar_busca_generica(config)
            listar(tipo)
        except (AttributeError, RuntimeError, ValueError, KeyError) as e:
            logging.error("Erro ao limpar busca para %s: %s", tipo, e)

    def _limpar_busca_deducao(self, config):
        entries = config.get("entries", {})
        for combo in [
            entries.get("material_combo"),
            entries.get("espessura_combo"),
            entries.get("canal_combo"),
        ]:
            if combo and hasattr(combo, "setCurrentIndex"):
                combo.setCurrentIndex(-1)

    def _limpar_busca_generica(self, config):
        busca_widget = config.get("busca")
        if busca_widget and hasattr(busca_widget, "clear"):
            busca_widget.clear()


limpar_busca = LimparBusca().limpar_busca


class WidgetUpdater:
    """Gerencia a atualização de comboboxes do CABEÇALHO."""

    def __init__(self):
        self.acoes = {
            "material": self._atualizar_material,
            "espessura": self._atualizar_espessura,
            "canal": self._atualizar_canal,
        }

    def atualizar(self, tipo):
        """Atualiza os widgets da interface conforme o tipo especificado."""
        if tipo in self.acoes:
            valores_preservar = self._preservar_valores(tipo)
            self.acoes[tipo]()
            self._restaurar_valores(valores_preservar)
            calcular_valores()

    def _preservar_valores(self, tipo):
        valores = {}
        if tipo == "material":
            valores["ESP_COMB"] = WidgetManager.get_widget_value(g.ESP_COMB)
            valores["CANAL_COMB"] = WidgetManager.get_widget_value(g.CANAL_COMB)
        elif tipo == "espessura":
            valores["CANAL_COMB"] = WidgetManager.get_widget_value(g.CANAL_COMB)
        return valores

    def _restaurar_valores(self, valores):
        for widget_name, valor in valores.items():
            if valor:
                widget = getattr(g, widget_name, None)
                if widget and hasattr(widget, "setCurrentText"):
                    widget.setCurrentText(valor)

    def _atualizar_material(self):
        """Atualiza combobox de materiais usando cache quando possível."""
        try:
            materiais = cache_manager.get_materiais()
            items = [material["nome"] for material in materiais]
            self._preencher_combobox_direto(g.MAT_COMB, items)
        except (AttributeError, ValueError, RuntimeError):
            self._preencher_combobox(
                g.MAT_COMB,
                lambda s: [
                    m.nome for m in s.query(Material).order_by(Material.nome).all()
                ],
            )

    def _atualizar_espessura(self):
        """Atualiza combobox de espessuras baseado no material selecionado."""
        material_nome = WidgetManager.get_widget_value(g.MAT_COMB)
        if not material_nome:
            if g.ESP_COMB:
                g.ESP_COMB.clear()
            return

        self._preencher_combobox(
            g.ESP_COMB,
            lambda s: [
                str(e.valor)
                for e in s.query(Espessura)
                .join(Deducao)
                .join(Material)
                .filter(Material.nome == material_nome)
                .order_by(Espessura.valor)
                .distinct()
            ],
        )

    def _atualizar_canal(self):
        """Atualiza combobox de canais baseado no material e espessura selecionados."""
        material_nome = WidgetManager.get_widget_value(g.MAT_COMB)
        espessura_valor = WidgetManager.get_widget_value(g.ESP_COMB)
        if not (material_nome and espessura_valor):
            if g.CANAL_COMB:
                g.CANAL_COMB.clear()
            return
        try:
            esp_val = float(espessura_valor)
            self._preencher_combobox(
                g.CANAL_COMB,
                lambda s: [
                    str(c.valor)
                    for c in s.query(Canal)
                    .join(Deducao)
                    .join(Material)
                    .join(Espessura)
                    .filter(Material.nome == material_nome, Espessura.valor == esp_val)
                    .order_by(Canal.valor)
                    .distinct()
                ],
            )
        except (ValueError, SQLAlchemyError):
            if g.CANAL_COMB:
                g.CANAL_COMB.clear()

    def _preencher_combobox_comum(self, combo, items_ou_query_func, usar_cache=False):
        """Método comum para preencher comboboxes, consolidando a lógica duplicada."""
        if not combo:
            return
        current_value = combo.currentText()
        combo.clear()

        try:
            if usar_cache or callable(items_ou_query_func):
                if callable(items_ou_query_func):
                    with get_session() as session:
                        items = items_ou_query_func(session)
                else:
                    items = items_ou_query_func
            else:
                items = items_ou_query_func

            combo.addItems(items)
            if current_value in items:
                combo.setCurrentText(current_value)
            else:
                combo.setCurrentIndex(-1)
        except SQLAlchemyError as e:
            logging.error("Erro ao preencher combobox: %s", e)

    def _preencher_combobox(self, combo, query_func):
        """Preenche combobox executando query no banco de dados."""
        self._preencher_combobox_comum(combo, query_func, usar_cache=False)

    def _preencher_combobox_direto(self, combo, items):
        """Preenche combobox diretamente com lista de itens (para uso com cache)."""
        self._preencher_combobox_comum(combo, items, usar_cache=True)


class FormWidgetUpdater:
    """Gerencia a atualização de comboboxes DENTRO DOS FORMULÁRIOS."""

    def atualizar(self, tipos):
        """Atualiza os comboboxes de acordo com os tipos especificados."""
        for tipo in tipos:
            if tipo == "material":
                try:
                    materiais = cache_manager.get_materiais()
                    items = [material["nome"] for material in materiais]
                    self._preencher_form_combo_direto(g.DED_MATER_COMB, items)
                except (AttributeError, ValueError, RuntimeError):
                    self._preencher_form_combo(
                        g.DED_MATER_COMB,
                        lambda s: [
                            m.nome
                            for m in s.query(Material).order_by(Material.nome).all()
                        ],
                    )
            elif tipo == "espessura":
                try:
                    espessuras = cache_manager.get_espessuras()
                    items = [str(espessura["valor"]) for espessura in espessuras]
                    self._preencher_form_combo_direto(g.DED_ESPES_COMB, items)
                except (AttributeError, ValueError, RuntimeError):
                    self._preencher_form_combo(
                        g.DED_ESPES_COMB,
                        lambda s: [
                            str(e.valor)
                            for e in s.query(Espessura).order_by(Espessura.valor).all()
                        ],
                    )
            elif tipo == "canal":
                try:
                    canais = cache_manager.get_canais()
                    items = sorted([canal["valor"] for canal in canais])
                    self._preencher_form_combo_direto(g.DED_CANAL_COMB, items)
                except (AttributeError, ValueError, RuntimeError):
                    self._preencher_form_combo(
                        g.DED_CANAL_COMB,
                        lambda s: [
                            str(c.valor)
                            for c in s.query(Canal).order_by(Canal.valor).all()
                        ],
                    )

    def _preencher_form_combo(self, combo, query_func):
        """Preenche combobox do formulário executando query no banco de dados."""
        if not combo:
            return
        current_text = combo.currentText()
        combo.clear()
        try:
            with get_session() as session:
                items = query_func(session)
                combo.addItems(items)
                if current_text in items:
                    combo.setCurrentText(current_text)
                else:
                    combo.setCurrentIndex(-1)
        except SQLAlchemyError as e:
            logging.error("Erro ao preencher combobox do formulário: %s", e)

    def _preencher_form_combo_direto(self, combo, items):
        """Preenche combobox do formulário diretamente com lista de itens (para uso com cache)."""
        if not combo:
            return
        current_text = combo.currentText()
        combo.clear()
        combo.addItems(items)
        if current_text in items:
            combo.setCurrentText(current_text)
        else:
            combo.setCurrentIndex(-1)


def obter_configuracoes():
    """Retorna um dicionário com as configurações de cada tipo de item."""
    return {
        "dedução": {
            "form": g.DEDUC_FORM,
            "lista": g.LIST_DED,
            "modelo": Deducao,
            "campos": {
                "valor": g.DED_VALOR_ENTRY,
                "observacao": g.DED_OBSER_ENTRY,
                "forca": g.DED_FORCA_ENTRY,
            },
            "valores": lambda d: (
                (
                    d.material.nome if d.material else "N/A",
                    d.espessura.valor if d.espessura else "N/A",
                    d.canal.valor if d.canal else "N/A",
                    d.valor,
                    d.observacao,
                    d.forca if d.forca is not None else "N/A",
                )
                if d.material and d.espessura and d.canal
                else None
            ),
            "ordem": Deducao.valor,
            "entries": {
                "material_combo": g.DED_MATER_COMB,
                "espessura_combo": g.DED_ESPES_COMB,
                "canal_combo": g.DED_CANAL_COMB,
            },
        },
        "material": {
            "form": g.MATER_FORM,
            "lista": g.LIST_MAT,
            "modelo": Material,
            "campos": {
                "nome": g.MAT_NOME_ENTRY,
                "densidade": g.MAT_DENS_ENTRY,
                "escoamento": g.MAT_ESCO_ENTRY,
                "elasticidade": g.MAT_ELAS_ENTRY,
            },
            "valores": lambda m: (m.nome, m.densidade, m.escoamento, m.elasticidade),
            "ordem": Material.nome,
            "busca": g.MAT_BUSCA_ENTRY,
            "campo_busca": Material.nome,
        },
        "espessura": {
            "form": g.ESPES_FORM,
            "lista": g.LIST_ESP,
            "modelo": Espessura,
            "campos": {"valor": g.ESP_VALOR_ENTRY},
            "valores": lambda e: (e.valor,),
            "ordem": Espessura.valor,
            "busca": g.ESP_BUSCA_ENTRY,
            "campo_busca": Espessura.valor,
        },
        "canal": {
            "form": g.CANAL_FORM,
            "lista": g.LIST_CANAL,
            "modelo": Canal,
            "campos": {
                "valor": g.CANAL_VALOR_ENTRY,
                "largura": g.CANAL_LARGU_ENTRY,
                "altura": g.CANAL_ALTUR_ENTRY,
                "comprimento_total": g.CANAL_COMPR_ENTRY,
                "observacao": g.CANAL_OBSER_ENTRY,
            },
            "valores": lambda c: (
                c.valor,
                c.largura,
                c.altura,
                c.comprimento_total,
                c.observacao,
            ),
            "ordem": Canal.valor,
            "busca": g.CANAL_BUSCA_ENTRY,
            "campo_busca": Canal.valor,
        },
        "usuario": {
            "form": g.USUAR_FORM,
            "lista": g.LIST_USUARIO,
            "modelo": Usuario,
            "valores": lambda u: (u.id, u.nome, u.role),
            "ordem": Usuario.nome,
            "busca": g.USUARIO_BUSCA_ENTRY,
            "campo_busca": Usuario.nome,
        },
    }


def limpar_dobras():
    """Limpa os valores das dobras e a dedução específica."""
    if hasattr(g, "VALORES_W"):
        for w in g.VALORES_W:
            for i in range(1, g.N):
                entry = getattr(g, f"aba{i}_entry_{w}", None)
                if entry and hasattr(entry, "clear"):
                    entry.clear()
    calcular_valores()
    if hasattr(g, "VALORES_W") and g.VALORES_W:
        primo_entry = getattr(g, f"aba1_entry_{g.VALORES_W[0]}", None)
        if primo_entry and hasattr(primo_entry, "setFocus"):
            primo_entry.setFocus()


def limpar_tudo():
    """Limpa todos os campos da interface principal."""
    for combo in [g.MAT_COMB, g.ESP_COMB, g.CANAL_COMB]:
        if combo:
            combo.setCurrentIndex(-1)
    for entry in [g.RI_ENTRY, g.COMPR_ENTRY, g.DED_ESPEC_ENTRY]:
        if entry:
            entry.clear()
    limpar_dobras()


def _coletar_dados_entrada() -> UIData:
    """Coleta todos os dados de entrada da UI."""
    return UIData(
        material_nome=WidgetManager.get_widget_value(g.MAT_COMB),
        espessura_str=WidgetManager.get_widget_value(g.ESP_COMB),
        canal_str=WidgetManager.get_widget_value(g.CANAL_COMB),
        raio_interno_str=WidgetManager.get_widget_value(g.RI_ENTRY),
        comprimento_str=WidgetManager.get_widget_value(g.COMPR_ENTRY),
        deducao_espec_str=WidgetManager.get_widget_value(g.DED_ESPEC_ENTRY),
        espessura=calculos.converter_para_float(
            WidgetManager.get_widget_value(g.ESP_COMB)
        ),
        raio_interno=calculos.converter_para_float(
            WidgetManager.get_widget_value(g.RI_ENTRY)
        ),
        comprimento=calculos.converter_para_float(
            WidgetManager.get_widget_value(g.COMPR_ENTRY)
        ),
        deducao_espec=calculos.converter_para_float(
            WidgetManager.get_widget_value(g.DED_ESPEC_ENTRY)
        ),
    )


def _atualizar_label(
    label,
    valor,
    formato="{:.2f}",
    estilo_sucesso="",
    estilo_erro="QLabel {color: red;}",
):
    """Função genérica para atualizar um QLineEdit ou QLabel."""
    if not WidgetManager.is_widget_valid(label):
        return
    if valor is None or valor == "":
        label.setText("")
        label.setStyleSheet(estilo_sucesso)
        return
    if isinstance(valor, str) and valor == "N/A":
        label.setText("N/A")
        label.setStyleSheet(estilo_erro)
        return
    try:
        label.setText(formato.format(float(valor)))
        label.setStyleSheet(estilo_sucesso)
    except (ValueError, TypeError):
        label.setText(str(valor))
        label.setStyleSheet(estilo_sucesso)


def _atualizar_deducao_ui(data: UIData) -> float:
    """Busca a dedução no DB, atualiza a UI e retorna a dedução a ser usada."""
    res_db = calculos.CalculoDeducaoDB().buscar(
        data.material_nome, data.espessura_str, data.canal_str
    )
    deducao_db_valor = ""
    if res_db:
        valor = (
            res_db.get("valor")
            if hasattr(res_db, "get")
            else getattr(res_db, "valor", None)
        )
        obs = (
            res_db.get("obs", "")
            if hasattr(res_db, "get")
            else getattr(res_db, "obs", "")
        )
        _atualizar_label(g.DED_LBL, valor, formato="{:.2f}")
        if g.OBS_LBL:
            g.OBS_LBL.setText(obs)
        deducao_db_valor = str(valor or "")
    else:
        _atualizar_label(g.DED_LBL, None)
        if g.OBS_LBL:
            g.OBS_LBL.setText("")

    return (
        data.deducao_espec
        if data.deducao_espec > 0
        else calculos.converter_para_float(deducao_db_valor)
    )


def _estilo(data: UIData):
    if not g.K_LBL or g.K_LBL.text() == "":
        if g.K_LBL:
            g.K_LBL.setToolTip(
                "Fator K calculado com base no raio interno. Clique para copiar."
            )
        return "QLabel {color: palette(text);}"
    if data.deducao_espec > 0:
        g.K_LBL.setToolTip(
            "Fator K calculado com dedução específica. Clique para copiar."
        )
        return "QLabel {color: blue;}"
    if not data.canal_str:
        g.K_LBL.setToolTip(
            "Fator K teórico com base na tabela Raio/Espessura. Clique para copiar."
        )
        return "QLabel {color: orange;}"
    g.K_LBL.setToolTip(
        "Fator K calculado com base no raio interno. Clique para copiar."
    )
    return "QLabel {color: palette(text);}"


def _atualizar_k_offset_ui(data: UIData, deducao_usada: float):
    """Calcula e atualiza os campos de Fator K e Offset."""
    res_k = (
        calculos.CalculoFatorK().calcular(
            data.espessura, data.raio_interno, deducao_usada
        )
        if data.espessura > 0 and data.raio_interno > 0
        else None
    )
    estilo = _estilo(data)
    _atualizar_label(
        g.K_LBL,
        (
            res_k.get("fator_k")
            if res_k
            else ("N/A" if data.espessura > 0 and data.raio_interno > 0 else None)
        ),
        estilo_sucesso=estilo,
    )
    _atualizar_label(
        g.OFFSET_LBL,
        (
            res_k.get("offset")
            if res_k
            else ("N/A" if data.espessura > 0 and data.raio_interno > 0 else None)
        ),
        estilo_sucesso=estilo,
    )


def _atualizar_parametros_auxiliares_ui(data: UIData, deducao_usada: float) -> float:
    """Calcula e atualiza Aba Mínima, Z Mínimo, Razão RI/E e retorna a aba mínima."""
    aba_min = calculos.CalculoAbaMinima().calcular(data.canal_str, data.espessura)
    _atualizar_label(
        g.ABA_EXT_LBL,
        aba_min if data.canal_str and data.espessura > 0 else None,
        formato="{:.0f}",
    )
    z_min = calculos.CalculoZMinimo().calcular(
        data.espessura, deducao_usada, data.canal_str
    )
    _atualizar_label(
        g.Z_EXT_LBL,
        z_min if data.espessura > 0 and data.canal_str else None,
        formato="{:.0f}",
    )
    razao = calculos.CalculoRazaoRIE().calcular(data.espessura, data.raio_interno)
    _atualizar_label(
        g.RAZAO_RIE_LBL,
        razao if data.espessura > 0 and data.raio_interno > 0 else None,
        formato="{:.1f}",
    )
    return float(aba_min) if aba_min is not None else 0.0


def _atualizar_forca_ui(data: UIData):
    """Calcula e atualiza o campo de Força."""
    if data.material_nome and data.espessura_str and data.canal_str:
        res_forca = calculos.CalculoForca().calcular(
            data.comprimento, data.espessura, data.material_nome, data.canal_str
        )
        forca_valor = res_forca.get("forca") if res_forca else "N/A"
        _atualizar_label(g.FORCA_LBL, forca_valor, formato="{:.0f}")

        # Aplicar cor baseada no valor da força
        if WidgetManager.is_widget_valid(g.FORCA_LBL) and forca_valor != "N/A":
            try:
                forca_num = float(forca_valor)
                if forca_num <= 250:
                    g.FORCA_LBL.setStyleSheet(
                        "QLabel { color: palette(text); }"
                    )  # Cor original
                elif 250 < forca_num <= 280:
                    g.FORCA_LBL.setStyleSheet("QLabel { color: orange; }")
                else:  # acima de 280
                    g.FORCA_LBL.setStyleSheet("QLabel { color: red; }")
            except (ValueError, TypeError):
                # Fallback para cor original
                g.FORCA_LBL.setStyleSheet("QLabel { color: palette(text); }")
        else:
            # Cor original se inválido ou N/A
            g.FORCA_LBL.setStyleSheet("QLabel { color: palette(text); }")

        compr_total = res_forca.get("comprimento_total") if res_forca else None
        excedido = (
            data.comprimento > 0
            and compr_total is not None
            and data.comprimento >= compr_total
        )
        if g.COMPR_ENTRY:
            g.COMPR_ENTRY.setStyleSheet("QLineEdit {color: red;}" if excedido else "")
    else:
        _atualizar_label(g.FORCA_LBL, None)
        if WidgetManager.is_widget_valid(g.FORCA_LBL):
            g.FORCA_LBL.setStyleSheet("")  # Cor original
        if g.COMPR_ENTRY:
            g.COMPR_ENTRY.setStyleSheet("QLineEdit{color: palette(window-text);}")

# pylint: disable=R0914


def _atualizar_coluna_dobras_ui(w: int, deducao_usada: float, aba_min: float):
    """Calcula e atualiza uma coluna inteira de dobras na UI."""
    valores = [
        calculos.converter_para_float(
            WidgetManager.get_widget_value(getattr(g, f"aba{i}_entry_{w}", None))
        )
        for i in range(1, g.N)
    ]
    res = calculos.CalculoDobra().calcular_coluna(valores, deducao_usada)
    total_abas = res.get("total_abas", 0) if res else 0
    blank = res.get("blank_total", 0) if res else 0

    # Verifica status das abas para lógica de bandeja
    abas_1_3_preenchidas = len(valores) >= 3 and all(v > 0 for v in valores[:3])
    abas_1_5_preenchidas = len(valores) >= 5 and all(v > 0 for v in valores[:5])

    for i in range(1, g.N):
        medida = res["resultados"][i - 1].get("medida") if res else None
        metade = res["resultados"][i - 1].get("metade") if res else None
        _atualizar_label(getattr(g, f"medidadobra{i}_label_{w}", None), medida)
        _atualizar_label(getattr(g, f"metadedobra{i}_label_{w}", None), metade)

        entry = getattr(g, f"aba{i}_entry_{w}", None)
        if WidgetManager.is_widget_valid(entry):
            val = valores[i - 1]
            invalida = aba_min is not None and 0 < val < aba_min

            # Alerta de bandeja: Apenas Aba 1 (se 1-3 estiverem ok)
            # e Aba 5 (se 1-5 estiverem ok), se valor > 20
            alerta_bandeja = (
                val > 20
                and (
                    (i == 1 and abas_1_3_preenchidas)
                    or (i == 5 and abas_1_5_preenchidas)
                )
            )

            if invalida:
                entry.setStyleSheet(
                    "QLineEdit { color: white; background-color: red; } "
                    "QLineEdit:hover { border: 1px solid darkred; } "
                    "QLineEdit:focus { border: 1px solid darkred; }"
                    "QToolTip { color: palette(text); background-color: palette(base); }"
                )
                entry.setToolTip(
                    f"Aba <b><span style='background-color:red; color:white;'>"
                    f"{val:.0f}mm</span></b> menor que a mínima <b>{aba_min:.0f}mm</b>."
                )
            elif alerta_bandeja:
                entry.setStyleSheet(
                    "QLineEdit { color: red; background-color: palette(base); font-weight: bold; }"
                    "QToolTip { color: palette(text); background-color: palette(base); }"
                )
                img_path = os.path.abspath(
                    "assets/canto_bandeja.PNG").replace("\\", "/")
                tooltip_text = (
                    f"<html><table width='200'>"
                    f"<tr><td align='center'>Se necessário o uso da ferramenta "
                    f"<b>'bigode'</b>, adicionar alívio de dobra se aba <b>"
                    f"<span style='color:red;'>maior que 20mm</span></b>.</td></tr>"
                    f"<tr><td align='center'><img src='{img_path}' width='200'></td></tr>"
                    f"</table></html>"
                )
                entry.setToolTip(tooltip_text)
            else:
                entry.setStyleSheet(
                    "QLineEdit { color: palette(text); background-color: palette(base); }"
                    "QToolTip { color: palette(text); background-color: palette(base); }"
                )
                entry.setToolTip(
                    f"Digite o valor da medida externa para a dobra {i} (Use ↑↓ para navegar)"
                )

    _atualizar_label(
        getattr(g, f"total_abas_label_{w}", None),
        total_abas if total_abas > 0 else None,
    )
    _atualizar_label(
        getattr(g, f"medida_blank_label_{w}", None), blank if blank > 0 else None
    )
    _atualizar_label(
        getattr(g, f"metade_blank_label_{w}", None), blank / 2 if blank > 0 else None
    )


def calcular_valores():
    """Função principal que orquestra todos os cálculos e atualizações da UI.

    SISTEMA OTIMIZADO: Execução direta sem delay desnecessário.
    """
    try:
        ui_data = _coletar_dados_entrada()
        deducao_usada = _atualizar_deducao_ui(ui_data)
        _atualizar_k_offset_ui(ui_data, deducao_usada)
        aba_min = _atualizar_parametros_auxiliares_ui(ui_data, deducao_usada)
        _atualizar_forca_ui(ui_data)

        if hasattr(g, "VALORES_W"):
            for w in g.VALORES_W:
                _atualizar_coluna_dobras_ui(w, deducao_usada, aba_min)
    except (AttributeError, ValueError, TypeError, SQLAlchemyError) as e:
        logging.error("Erro em calcular_valores: %s\n%s", e, traceback.format_exc())


def todas_funcoes():
    """Executa a atualização completa da interface, incluindo comboboxes.

    Inicializa todos os comboboxes principais na ordem correta:
    1. Material (independente)
    2. Espessura (depende do material)
    3. Canal (depende do material e espessura)

    Usada na inicialização da aplicação e reload da interface.
    """
    updater = WidgetUpdater()
    for tipo in ["material", "espessura", "canal"]:
        updater.atualizar(tipo)


def focus_next_entry(current_index, w):
    """Move o foco para o próximo campo de entrada."""
    next_entry = getattr(g, f"aba{current_index + 1}_entry_{w}", None)
    if next_entry:
        next_entry.setFocus()


def focus_previous_entry(current_index, w):
    """Move o foco para o campo de entrada anterior."""
    prev_entry = getattr(g, f"aba{current_index - 1}_entry_{w}", None)
    if prev_entry:
        prev_entry.setFocus()


def canal_tooltip():
    """Atualiza o tooltip do combobox de canais, usando cache quando possível."""
    if not g.CANAL_COMB:
        return
    canal_str = WidgetManager.get_widget_value(g.CANAL_COMB)
    tooltip = "Selecione o canal de dobra."
    if canal_str:
        try:
            canais = cache_manager.get_canais()
            canal_info = next(
                (c for c in canais if str(c.get("valor")) == str(canal_str)), None
            )
            if canal_info:
                largura = (
                    canal_info.get("largura")
                    if canal_info.get("largura") is not None
                    else "N/A"
                )
                altura = (
                    canal_info.get("altura")
                    if canal_info.get("altura") is not None
                    else "N/A"
                )
                comp = (
                    canal_info.get("comprimento_total")
                    if canal_info.get("comprimento_total") is not None
                    else "N/A"
                )
                obs = (
                    canal_info.get("observacao")
                    if canal_info.get("observacao")
                    else "N/A"
                )
                tooltip = (
                    f"Largura: {largura}\n"
                    f"Altura: {altura}\n"
                    f"Comprimento total: {comp}\n"
                    f"Obs: {obs}"
                )
            else:
                with get_session() as session:
                    canal_obj = session.query(Canal).filter_by(valor=canal_str).first()
                    if canal_obj:
                        largura = (
                            canal_obj.largura
                            if canal_obj.largura is not None
                            else "N/A"
                        )
                        altura = (
                            canal_obj.altura if canal_obj.altura is not None else "N/A"
                        )
                        comp = (
                            canal_obj.comprimento_total
                            if canal_obj.comprimento_total is not None
                            else "N/A"
                        )
                        obs = canal_obj.observacao if canal_obj.observacao else "N/A"
                        tooltip = (
                            f"Largura: {largura}\n"
                            f"Altura: {altura}\n"
                            f"Comprimento total: {comp}\n"
                            f"Obs: {obs}"
                        )
                    else:
                        tooltip = "Canal não encontrado."
        except SQLAlchemyError as e:
            tooltip = f"Erro ao buscar dados do canal: {e}"
    g.CANAL_COMB.setToolTip(tooltip)
