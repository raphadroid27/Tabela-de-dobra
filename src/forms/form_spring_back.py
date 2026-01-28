"""Formulário para o cálculo de Spring Back."""

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QLabel,
    QGroupBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from src.config import globals as g
from src.forms.common.ui_helpers import configurar_dialogo_padrao
from src.forms.common.form_manager import BaseSingletonFormManager
from src.forms.form_razao_rie import LABEL_ALTURA, COLUNA_RAZAO_LARGURA
from src.models.models import Material
from src.utils.banco_dados import get_session
from src.utils.calculos import converter_para_float, calcular_spring_back
from src.utils.themed_widgets import ThemedDialog
# importar utilitário para ajustar margens/espacamentos
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco
# usar função de posicionamento
from src.utils.janelas import Janela
# botão removido — estilo de botão não é mais necessário aqui


def create_spring_back_form(root: Optional[QWidget] = None) -> ThemedDialog:
    """Create the Spring Back form using QDialog with custom title bar."""
    form_spring = ThemedDialog(root)
    form_spring.setWindowTitle("Cálculo de Spring Back")
    form_spring.setFixedSize(300, 320)
    configurar_dialogo_padrao(form_spring, ICON_PATH)
    form_spring.setWindowFlags(Qt.WindowType.WindowCloseButtonHint)

    Janela.posicionar_janela(form_spring)

    # Layout vertical: barra de título customizada + conteúdo grid
    vlayout = QVBoxLayout(form_spring)
    aplicar_medida_borda_espaco(vlayout)

    conteudo = QWidget()
    layout = QGridLayout(conteudo)
    aplicar_medida_borda_espaco(layout)

    # carregar materiais e mapear propriedades
    materiais = []
    mat_map: dict = {}
    with get_session() as session:
        for m in session.query(Material).all():
            name = str(m.nome)
            materiais.append(name)
            mat_map[name] = {"Y": m.escoamento, "E": m.elasticidade}

    # helper para criar labels de resultado no estilo do formulário
    def _criar_label_resultado() -> QLabel:
        lbl = QLabel("")
        lbl.setMinimumWidth(COLUNA_RAZAO_LARGURA)
        lbl.setFrameShape(QLabel.Shape.Panel)
        lbl.setFrameShadow(QLabel.Shadow.Sunken)
        lbl.setFixedHeight(LABEL_ALTURA)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    # GroupBox para parâmetros de entrada (material, dimensões e propriedades)
    params_gb = QGroupBox("Parâmetros")
    params_layout = QGridLayout(params_gb)
    aplicar_medida_borda_espaco(params_layout)

    label_material = QLabel("Material:")
    label_material.setObjectName("label_titulo")
    params_layout.addWidget(label_material, 0, 0)

    label_t = QLabel("Espessura [mm]:")
    label_t.setObjectName("label_titulo")
    params_layout.addWidget(label_t, 0, 1)

    g.MAT_COMB = QComboBox()
    g.MAT_COMB.addItems(materiais)
    params_layout.addWidget(g.MAT_COMB, 1, 0)

    spin_t = QLineEdit()
    validator_t = QDoubleValidator(0.01, 100.0, 6, spin_t)
    validator_t.setNotation(QDoubleValidator.StandardNotation)
    spin_t.setValidator(validator_t)
    params_layout.addWidget(spin_t, 1, 1)

    label_rf = QLabel("Raio Final [mm]:")
    label_rf.setObjectName("label_titulo")
    params_layout.addWidget(label_rf, 2, 0)

    label_a2 = QLabel("Ângulo Final [°]:")
    label_a2.setObjectName("label_titulo")
    params_layout.addWidget(label_a2, 2, 1)

    spin_rf = QLineEdit()
    validator_rf = QDoubleValidator(0.0, 10000.0, 6, spin_rf)
    validator_rf.setNotation(QDoubleValidator.StandardNotation)
    spin_rf.setValidator(validator_rf)
    params_layout.addWidget(spin_rf, 3, 0)

    spin_a2 = QLineEdit()
    validator_a2 = QDoubleValidator(0.0, 360.0, 6, spin_a2)
    validator_a2.setNotation(QDoubleValidator.StandardNotation)
    spin_a2.setValidator(validator_a2)
    params_layout.addWidget(spin_a2, 3, 1)

    lbl_y_title = QLabel("Escoamento [MPa]:")
    lbl_y_title.setObjectName("label_titulo")
    params_layout.addWidget(lbl_y_title, 4, 0)

    lbl_e_title = QLabel("Elasticidade [GPa]:")
    lbl_e_title.setObjectName("label_titulo")
    params_layout.addWidget(lbl_e_title, 4, 1)

    # labels de resultado para Y e E (estilo painel)
    lbl_y = _criar_label_resultado()
    params_layout.addWidget(lbl_y, 5, 0)

    lbl_e = _criar_label_resultado()
    lbl_e.setText("")
    params_layout.addWidget(lbl_e, 5, 1)

    layout.addWidget(params_gb, 0, 0, 1, 2)

    # Removido botão "Calcular" — cálculo será automático ao alterar dados

    # Resultados dentro de um GroupBox
    resultados_gb = QGroupBox("Resultados")
    resultados_layout = QGridLayout(resultados_gb)
    aplicar_medida_borda_espaco(resultados_layout)

    res_ks_title = QLabel("Ks:")
    res_ks_title.setObjectName("label_titulo")
    resultados_layout.addWidget(res_ks_title, 0, 0)

    res_ks = _criar_label_resultado()
    resultados_layout.addWidget(res_ks, 0, 1)

    res_ri_title = QLabel("Raio Inicial Ri [mm]:")
    res_ri_title.setObjectName("label_titulo")
    resultados_layout.addWidget(res_ri_title, 1, 0)

    res_ri = _criar_label_resultado()
    resultados_layout.addWidget(res_ri, 1, 1)

    res_a1_title = QLabel("Ângulo Inicial α1 [°]:")
    res_a1_title.setObjectName("label_titulo")
    resultados_layout.addWidget(res_a1_title, 2, 0)

    res_a1 = _criar_label_resultado()
    resultados_layout.addWidget(res_a1, 2, 1)

    layout.addWidget(resultados_gb, 7, 0, 1, 2)

    # nota informativa removida conforme solicitado

    def _format_val(v: Optional[float], precision: int = 4) -> str:
        if v is None:
            return ""
        try:
            return f"{v:.{precision}f}"
        except (TypeError, ValueError):
            return str(v)

    def _on_material_changed(name: str) -> None:
        props = mat_map.get(name)
        if not props:
            lbl_y.setText("")
            lbl_e.setText("")
            return
        y = props.get("Y")
        e = props.get("E")
        lbl_y.setText(_format_val(y, 0) if y is not None else "")
        lbl_e.setText(_format_val(e, 0) if e is not None else "")

    def _calculate() -> None:
        # obter propriedades
        name = g.MAT_COMB.currentText()
        props = mat_map.get(name) if name else None
        if not props:
            res_ks.setText("")
            res_ri.setText("")
            res_a1.setText("")
            return

        y = props.get("Y")
        e = props.get("E")
        # obter valores das QLineEdit (reutiliza conversor genérico)
        t = converter_para_float(spin_t.text(), 0.0)
        rf = converter_para_float(spin_rf.text(), 0.0)
        a2 = converter_para_float(spin_a2.text(), 0.0)

        resultados = calcular_spring_back(y, e, t, rf, a2)
        ks_val = resultados.get("ks")
        ri_val = resultados.get("ri")
        a1_val = resultados.get("a1")

        res_ks.setText(_format_val(ks_val, 6))
        res_ri.setText(_format_val(ri_val, 4))
        res_a1.setText(_format_val(a1_val, 4))

    # conectar sinais: recalcular automaticamente quando dados sensíveis mudarem
    g.MAT_COMB.currentTextChanged.connect(_on_material_changed)
    g.MAT_COMB.currentTextChanged.connect(_calculate)
    spin_t.textChanged.connect(lambda _: _calculate())
    spin_rf.textChanged.connect(lambda _: _calculate())
    spin_a2.textChanged.connect(lambda _: _calculate())

    # inicializar campos com o primeiro material se houver
    if materiais:
        _on_material_changed(materiais[0])
        # calcular inicialmente com os valores carregados
        _calculate()

    conteudo.setLayout(layout)
    vlayout.addWidget(conteudo)

    return form_spring


class FormManager(BaseSingletonFormManager):
    """Gerenciador de instância única para o formulário de Spring Back."""

    FORM_CLASS = staticmethod(lambda parent=None: create_spring_back_form(parent))


def main(parent=None):
    """Mostra o formulário de Spring Back (ponto de entrada usado pelo app)."""
    FormManager.show_form(parent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main(None)
    sys.exit(app.exec())
