"""
Módulo de Interface para o Aplicativo de Dobras.

Este módulo contém funções que interagem diretamente com a interface gráfica
(widgets PySide6). Ele é responsável por:
- Orquestrar os cálculos do módulo `calculos`.
- Ler os dados da UI, chamar a lógica de cálculo e atualizar os widgets com os resultados.
- Gerenciar a aparência (estilos, tooltips) dos widgets.
- Lidar com ações diretas na interface, como limpeza de campos e cópia de valores.
"""

from src.utils.widget import WidgetManager
from src.utils.cache_manager import (
    cache_com_ttl,
    cache_manager,
    limpar_cache_expirado,
    limpar_cache,
)
import logging
from dataclasses import dataclass
from functools import partial

import pyperclip
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QTreeWidgetItem

from src.config import globals as g
from src.models.models import Canal, Deducao, Espessura, Material, Usuario
from src.utils import calculos
from src.utils.banco_dados import session

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


# --- Classes de Manipulação da Interface (CopyManager, ListManager, etc.) ---


class CopyManager:
    """Gerencia operações de cópia de valores dos widgets."""

    def __init__(self):
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
        label_func = self.configuracoes.get(tipo, {}).get("label")
        if not label_func:
            return
        label = label_func(numero, w)
        if not label or not hasattr(label, "text"):
            return

        calcular_valores()
        texto_original = label.text().replace(" Copiado!", "")
        if not texto_original.strip():
            return

        pyperclip.copy(texto_original)
        label.setText(f"{texto_original} Copiado!")
        label.setStyleSheet("QLabel { color: green; }")

        QTimer.singleShot(5000, partial(self._restaurar_label, label, texto_original))

    def _restaurar_label(self, label, texto):
        """Restaura o texto e estilo original do label."""

        data = _coletar_dados_entrada()
        estilo = _estilo(data)

        if label and hasattr(label, "text") and "Copiado!" in label.text():
            label.setText(texto)
            label.setStyleSheet(estilo)


copiar = CopyManager().copiar


class ListManager:
    """Gerencia operações de listagem de dados do banco na interface."""

    def __init__(self):
        self.configuracoes = None

    def listar(self, tipo):
        """
        Lista os itens do banco de dados na interface gráfica, de acordo com o tipo informado.
        """
        self.configuracoes = obter_configuracoes()
        if not self.configuracoes or tipo not in self.configuracoes:
            return

        config = self.configuracoes[tipo]
        lista_widget = config.get("lista")
        if not lista_widget:
            return

        lista_widget.clear()
        itens = session.query(config["modelo"]).order_by(config["ordem"]).all()

        for item in itens:
            if tipo == "dedução" and not all(
                [item.material, item.espessura, item.canal]
            ):
                continue
            valores = config["valores"](item)
            valores_str = [str(v) if v is not None else "" for v in valores]
            item_widget = QTreeWidgetItem(valores_str)
            lista_widget.addTopLevelItem(item_widget)


listar = ListManager().listar


class LimparBusca:
    """Classe para limpar campos de busca dos formulários."""

    def limpar_busca(self, tipo):
        """
        Limpa os campos de busca e atualiza a lista correspondente.
        """
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
        combos = [
            entries.get("material_combo"),
            entries.get("espessura_combo"),
            entries.get("canal_combo"),
        ]
        for combo in combos:
            if combo and hasattr(combo, "setCurrentIndex"):
                combo.setCurrentIndex(-1)

    def _limpar_busca_generica(self, config):
        busca_widget = config.get("busca")
        if busca_widget and hasattr(busca_widget, "clear"):
            busca_widget.clear()


limpar_busca = LimparBusca().limpar_busca


class WidgetUpdater:
    """Gerencia a atualização de comboboxes do CABEÇALHO e seus dados dependentes."""

    def __init__(self):
        self.acoes = {
            "material": self._atualizar_material,
            "espessura": self._atualizar_espessura,
            "canal": self._atualizar_canal,
            "dedução": self._atualizar_deducao,
        }

    def atualizar(self, tipo):
        """
        Atualiza os widgets da interface conforme o tipo especificado.
        """
        if tipo not in self.acoes:
            return

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
        if hasattr(g, "MAT_COMB") and g.MAT_COMB:
            current_value = g.MAT_COMB.currentText()
            g.MAT_COMB.clear()
            materiais = [
                m.nome for m in session.query(Material).order_by(Material.nome).all()
            ]
            g.MAT_COMB.addItems(materiais)
            index = g.MAT_COMB.findText(current_value)
            g.MAT_COMB.setCurrentIndex(index)

    def _atualizar_espessura(self):
        if hasattr(g, "ESP_COMB") and g.ESP_COMB:
            current_value = g.ESP_COMB.currentText()
            g.ESP_COMB.clear()
            material_nome = WidgetManager.get_widget_value(g.MAT_COMB)
            if material_nome:
                material_obj = (
                    session.query(Material).filter_by(nome=material_nome).first()
                )
                if material_obj:
                    espessuras = (
                        session.query(Espessura)
                        .join(Deducao)
                        .filter(Deducao.material_id == material_obj.id)
                        .order_by(Espessura.valor)
                        .distinct()
                    )
                    g.ESP_COMB.addItems([str(e.valor) for e in espessuras])

            index = g.ESP_COMB.findText(current_value)
            g.ESP_COMB.setCurrentIndex(index)

    def _atualizar_canal(self):
        if hasattr(g, "CANAL_COMB") and g.CANAL_COMB:
            current_value = g.CANAL_COMB.currentText()
            g.CANAL_COMB.clear()
            material_nome = WidgetManager.get_widget_value(g.MAT_COMB)
            espessura_valor = WidgetManager.get_widget_value(g.ESP_COMB)
            if material_nome and espessura_valor:
                try:
                    espessura_obj = (
                        session.query(Espessura)
                        .filter_by(valor=float(espessura_valor))
                        .first()
                    )
                    material_obj = (
                        session.query(Material).filter_by(nome=material_nome).first()
                    )
                    if espessura_obj and material_obj:
                        canais = (
                            session.query(Canal)
                            .join(Deducao)
                            .filter(
                                Deducao.espessura_id == espessura_obj.id,
                                Deducao.material_id == material_obj.id,
                            )
                            .order_by(Canal.valor)
                            .distinct()
                        )
                        g.CANAL_COMB.addItems([str(c.valor) for c in canais])
                except ValueError:
                    pass

            index = g.CANAL_COMB.findText(current_value)
            g.CANAL_COMB.setCurrentIndex(index)

    def _atualizar_deducao(self):
        """Passa a responsabilidade de atualização para o fluxo principal de cálculo."""


class FormWidgetUpdater:
    """Gerencia a atualização de comboboxes APENAS DENTRO DOS FORMULÁRIOS."""

    def __init__(self):
        """Inicializa o despachante de ações."""
        self.acoes = {
            "material": self._atualizar_material_form,
            "espessura": self._atualizar_espessura_form,
            "canal": self._atualizar_canal_form,
        }

    def atualizar(self, tipos):
        """Atualiza os comboboxes do formulário para os tipos especificados."""
        for tipo in tipos:
            if tipo in self.acoes:
                self.acoes[tipo]()

    def _atualizar_material_form(self):
        """Atualiza o combobox de material no formulário de dedução."""
        if hasattr(g, "DED_MATER_COMB") and g.DED_MATER_COMB:
            materiais = [
                m.nome for m in session.query(Material).order_by(Material.nome).all()
            ]
            current_value_form = g.DED_MATER_COMB.currentText()
            g.DED_MATER_COMB.clear()
            g.DED_MATER_COMB.addItems(materiais)
            if current_value_form in materiais:
                g.DED_MATER_COMB.setCurrentText(current_value_form)
            else:
                g.DED_MATER_COMB.setCurrentIndex(-1)

    def _atualizar_espessura_form(self):
        """Atualiza o combobox de espessura no formulário de dedução."""
        if hasattr(g, "DED_ESPES_COMB") and g.DED_ESPES_COMB:
            espessuras = [
                str(e.valor)
                for e in session.query(Espessura).order_by(Espessura.valor).all()
            ]
            g.DED_ESPES_COMB.clear()
            g.DED_ESPES_COMB.addItems(espessuras)
            g.DED_ESPES_COMB.setCurrentIndex(-1)

    def _atualizar_canal_form(self):
        """Atualiza o combobox de canal no formulário de dedução."""
        if hasattr(g, "DED_CANAL_COMB") and g.DED_CANAL_COMB:
            canais = [
                str(c.valor) for c in session.query(Canal).order_by(Canal.valor).all()
            ]
            g.DED_CANAL_COMB.clear()
            g.DED_CANAL_COMB.addItems(canais)
            g.DED_CANAL_COMB.setCurrentIndex(-1)


# --- OBTER CONFIGURAÇÕES ---


def obter_configuracoes():
    """
    Retorna um dicionário com as configurações de cada tipo de item.
    Esta função mapeia os tipos de dados para os widgets da UI correspondentes,
    sendo essencial para a camada de handlers.
    """
    return {
        "principal": {
            "form": g.PRINC_FORM,
        },
        "dedução": {
            "form": g.DEDUC_FORM,
            "lista": g.LIST_DED,
            "modelo": Deducao,
            "campos": {
                "valor": g.DED_VALOR_ENTRY,
                "observacao": g.DED_OBSER_ENTRY,
                "forca": g.DED_FORCA_ENTRY,
            },
            "item_id": Deducao.id,
            "valores": lambda d: (
                d.material.nome,
                d.espessura.valor,
                d.canal.valor,
                d.valor,
                d.observacao,
                d.forca,
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
            "item_id": Material.id,
            "valores": lambda m: (m.nome, m.densidade, m.escoamento, m.elasticidade),
            "ordem": Material.id,
            "entry": g.MAT_NOME_ENTRY,
            "busca": g.MAT_BUSCA_ENTRY,
            "campo_busca": Material.nome,
        },
        "espessura": {
            "form": g.ESPES_FORM,
            "lista": g.LIST_ESP,
            "modelo": Espessura,
            "campos": {"valor": g.ESP_VALOR_ENTRY},
            "item_id": Espessura.id,
            "valores": lambda e: (e.valor,),
            "ordem": Espessura.valor,
            "entry": g.ESP_VALOR_ENTRY,
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
            "item_id": Canal.id,
            "valores": lambda c: (
                c.valor,
                c.largura,
                c.altura,
                c.comprimento_total,
                c.observacao,
            ),
            "ordem": Canal.valor,
            "entry": g.CANAL_VALOR_ENTRY,
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


# --- FUNÇÕES DE LIMPEZA ---


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
        primeiro_entry = getattr(g, f"aba1_entry_{g.VALORES_W[0]}", None)
        if primeiro_entry and hasattr(primeiro_entry, "setFocus"):
            primeiro_entry.setFocus()


def limpar_tudo():
    """Limpa todos os campos e labels da interface principal."""
    if hasattr(g, "MAT_COMB") and g.MAT_COMB:
        g.MAT_COMB.setCurrentIndex(-1)
    for combo_global in [g.ESP_COMB, g.CANAL_COMB]:
        if combo_global and hasattr(combo_global, "clear"):
            combo_global.clear()

    for entry_global in [g.RI_ENTRY, g.COMPR_ENTRY]:
        if entry_global and hasattr(entry_global, "clear"):
            entry_global.clear()

    ded_espec_entry = getattr(g, "DED_ESPEC_ENTRY", None)
    if ded_espec_entry and hasattr(ded_espec_entry, "clear"):
        ded_espec_entry.clear()

    limpar_dobras()


# --- ORQUESTRADOR DE CÁLCULOS E ATUALIZAÇÕES (REATORADO) ---


def _coletar_dados_entrada() -> UIData:
    """Coleta todos os dados de entrada da UI e os retorna em uma estrutura."""
    material_nome = WidgetManager.get_widget_value(g.MAT_COMB)
    espessura_str = WidgetManager.get_widget_value(g.ESP_COMB)
    canal_str = WidgetManager.get_widget_value(g.CANAL_COMB)
    raio_interno_str = WidgetManager.get_widget_value(g.RI_ENTRY)
    comprimento_str = WidgetManager.get_widget_value(g.COMPR_ENTRY)
    deducao_espec_str = WidgetManager.get_widget_value(g.DED_ESPEC_ENTRY)

    return UIData(
        material_nome=material_nome,
        espessura_str=espessura_str,
        canal_str=canal_str,
        raio_interno_str=raio_interno_str,
        comprimento_str=comprimento_str,
        deducao_espec_str=deducao_espec_str,
        espessura=calculos.converter_para_float(espessura_str),
        raio_interno=calculos.converter_para_float(raio_interno_str),
        comprimento=calculos.converter_para_float(comprimento_str),
        deducao_espec=calculos.converter_para_float(deducao_espec_str),
    )


def _atualizar_label(
    label, valor, formato="{:.2f}", estilo_sucesso="", estilo_erro="color: red;"
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
    deducao_label_str = ""

    if res_db:
        _atualizar_label(g.DED_LBL, res_db.get("valor"), formato="{:.2f}")
        if g.OBS_LBL:
            g.OBS_LBL.setText(res_db.get("obs", ""))
        deducao_label_str = str(res_db.get("valor", ""))
    else:
        _atualizar_label(g.DED_LBL, None)
        if g.OBS_LBL:
            g.OBS_LBL.setText("")

    return (
        data.deducao_espec
        if data.deducao_espec > 0
        else calculos.converter_para_float(deducao_label_str)
    )


def _estilo(data: UIData):
    estilo_k = ""  # Definição padrão

    # Define o estilo do Fator K conforme a origem da dedução
    if g.K_LBL.text() == "":
        g.K_LBL.setToolTip("Fator K calculado com base no raio interno.")
        g.K_LBL.setStyleSheet("")
    elif data.deducao_espec > 0:
        estilo_k = "QLabel {color: blue;}"
        g.K_LBL.setToolTip("Fator K calculado com dedução específica.")
    elif data.canal_str == "":
        estilo_k = "QLabel {color: orange;}"
        g.K_LBL.setToolTip("Fator K teórico com base na tabela Raio/Espessura.")
    else:
        g.K_LBL.setToolTip("Fator K calculado com base no raio interno.")

    return estilo_k


def _atualizar_k_offset_ui(data: UIData, deducao_usada: float):
    """Calcula e atualiza os campos de Fator K e Offset."""
    res_k = calculos.CalculoFatorK().calcular(
        data.espessura, data.raio_interno, deducao_usada
    )

    estilo_k_offset = _estilo(data)

    if res_k:
        _atualizar_label(g.K_LBL, res_k["fator_k"], estilo_sucesso=estilo_k_offset)
        _atualizar_label(g.OFFSET_LBL, res_k["offset"], estilo_sucesso=estilo_k_offset)
    else:
        _atualizar_label(g.K_LBL, None)
        _atualizar_label(g.OFFSET_LBL, None)


def _atualizar_parametros_auxiliares_ui(data: UIData, deducao_usada: float) -> float:
    """Calcula e atualiza Aba Mínima, Z Mínimo, Razão RI/E e retorna a aba mínima."""
    aba_min = calculos.CalculoAbaMinima().calcular(data.canal_str, data.espessura)
    _atualizar_label(g.ABA_EXT_LBL, aba_min, formato="{:.0f}")

    z_min = calculos.CalculoZMinimo().calcular(
        data.espessura, deducao_usada, data.canal_str
    )
    _atualizar_label(g.Z_EXT_LBL, z_min, formato="{:.0f}")

    razao = calculos.CalculoRazaoRIE().calcular(data.espessura, data.raio_interno)
    _atualizar_label(g.RAZAO_RIE_LBL, razao, formato="{:.1f}")

    return aba_min


def _atualizar_forca_ui(data: UIData):
    """Calcula e atualiza o campo de Força."""
    res_forca = calculos.CalculoForca().calcular(
        data.comprimento, data.espessura, data.material_nome, data.canal_str
    )
    if res_forca:
        _atualizar_label(g.FORCA_LBL, res_forca.get("forca"), formato="{:.0f}")
        canal_obj = res_forca.get("canal_obj")
        comprimento_total = (
            getattr(canal_obj, "comprimento_total", None) if canal_obj else None
        )

        is_comprimento_excedido = (
            data.comprimento > 0
            and comprimento_total is not None
            and data.comprimento >= comprimento_total
        )
        if g.COMPR_ENTRY:
            g.COMPR_ENTRY.setStyleSheet(
                "color: red;" if is_comprimento_excedido else ""
            )
    else:
        _atualizar_label(g.FORCA_LBL, None)
        if g.COMPR_ENTRY:
            g.COMPR_ENTRY.setStyleSheet("")


def _atualizar_coluna_dobras_ui(w: int, deducao_usada: float, aba_min: float):
    """Calcula e atualiza uma coluna inteira de dobras na UI."""
    valores_dobras = [
        calculos.converter_para_float(
            WidgetManager.get_widget_value(getattr(g, f"aba{i}_entry_{w}", None))
        )
        for i in range(1, g.N)
    ]

    res_coluna = calculos.CalculoDobra().calcular_coluna(valores_dobras, deducao_usada)

    blank_total = 0
    if res_coluna:
        blank_total = res_coluna.get("blank_total", 0)
        for i, res in enumerate(res_coluna.get("resultados", []), 1):
            _atualizar_label(
                getattr(g, f"medidadobra{i}_label_{w}", None), res.get("medida")
            )
            _atualizar_label(
                getattr(g, f"metadedobra{i}_label_{w}", None), res.get("metade")
            )
    else:
        # Se res_coluna for None (ex: dedução <= 0), limpa os labels de resultado
        for i in range(1, g.N):
            _atualizar_label(getattr(g, f"medidadobra{i}_label_{w}", None), None)
            _atualizar_label(getattr(g, f"metadedobra{i}_label_{w}", None), None)

    _atualizar_label(
        getattr(g, f"medida_blank_label_{w}", None),
        blank_total if blank_total > 0 else None,
    )
    _atualizar_label(
        getattr(g, f"metade_blank_label_{w}", None),
        blank_total / 2 if blank_total > 0 else None,
    )

    for i, valor_dobra in enumerate(valores_dobras, 1):
        entry = getattr(g, f"aba{i}_entry_{w}", None)
        if WidgetManager.is_widget_valid(entry):
            is_aba_invalida = (
                # pylint: disable= R1716:
                valor_dobra > 0
                and aba_min is not None
                and valor_dobra < aba_min
            )
            if is_aba_invalida:
                entry.setStyleSheet("color: white; background-color: red;")
                entry.setToolTip(
                    f"Aba ({valor_dobra}) menor que a mínima ({aba_min:.0f})."
                )
            else:
                entry.setStyleSheet("")
                entry.setToolTip("Insira o valor da dobra.")


def calcular_valores():
    """
    Função principal que orquestra todos os cálculos e atualizações da UI.
    Agora ela delega as tarefas para funções auxiliares menores.
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

    except (AttributeError, RuntimeError, ValueError, KeyError, TypeError) as e:
        logging.error("Erro inesperado em calcular_valores: %s", e)
        logging.debug("Detalhes do erro:", exc_info=True)


def todas_funcoes():
    """Executa a atualização completa da interface, incluindo comboboxes."""
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
    """Atualiza o tooltip do combobox de canais."""
    if not g.CANAL_COMB:
        return
    canal_str = WidgetManager.get_widget_value(g.CANAL_COMB)
    if not canal_str:
        g.CANAL_COMB.setToolTip("Selecione o canal de dobra.")
        return
    canal_obj = session.query(Canal).filter_by(valor=canal_str).first()
    if canal_obj:
        obs = getattr(canal_obj, "observacao", "N/A")
        comp = getattr(canal_obj, "comprimento_total", "N/A")
        g.CANAL_COMB.setToolTip(f"Obs: {obs}\nComprimento total: {comp}")
    else:
        g.CANAL_COMB.setToolTip("Canal não encontrado.")


atualizar_widgets = WidgetUpdater().atualizar
atualizar_comboboxes_formulario = FormWidgetUpdater().atualizar
