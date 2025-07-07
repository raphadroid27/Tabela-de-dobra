"""
Funções auxiliares para o aplicativo de cálculo de dobras.
"""
from math import pi
import re
from src.config import globals as g
from src.models.models import Canal
from src.utils.banco_dados import session


def verificar_widget_inicializado(widget, metodo='get', default_value=''):
    """
    Verifica se um widget está inicializado antes de chamar seus métodos.

    Args:
        widget: O widget a ser verificado
        metodo: O método a ser chamado ('get', 'text', 'currentText')
        default_value: Valor padrão caso o widget não esteja inicializado

    Returns:
        O resultado do método ou o valor padrão
    """
    if widget is None:
        return default_value

    try:
        if metodo == 'get' or metodo == 'text':
            # PySide6 QLineEdit usa text()
            if hasattr(widget, 'text'):
                return widget.text()
            elif hasattr(widget, 'currentText'):
                return widget.currentText()
        elif metodo == 'currentText':
            if hasattr(widget, 'currentText'):
                result = widget.currentText()
                return result if result else default_value
        elif metodo == 'cget':
            # Para PySide6 QLabel, usa text()
            if hasattr(widget, 'text'):
                return widget.text()
        return default_value
    except (AttributeError, TypeError):
        return default_value


def calcular_k_offset():
    """
    Calcula o fator K com base nos valores de espessura, dedução e raio interno.
    O fator K é usado para calcular o desenvolvimento de dobras considerando o
    alongamento do material.

    Fórmulas utilizadas:
    - Fator K personalizado: K = (4 × (espessura - (dedução / 2) + raio_interno) -
      (π × raio_interno)) / (π × espessura)
      (usado sempre que há dedução disponível)
    - Fator K padrão baseado na razão raio/espessura (usando tabela de referência)
      (usado apenas quando não há dedução disponível)
    - Offset = Fator K × Espessura

    Atualiza os labels correspondentes com os valores calculados.
    """
    try:
        # Obtém os valores dos widgets e valida
        espessura_text = verificar_widget_inicializado(
            g.ESP_COMB, 'currentText', '0') or '0'
        raio_interno_str = verificar_widget_inicializado(
            g.RI_ENTRY, 'text', '0') or '0'
        deducao_espec_str = verificar_widget_inicializado(
            g.DED_ESPEC_ENTRY, 'text', '0') or '0'

        # Converte valores para float, tratando vírgulas
        espessura = float(espessura_text.replace(
            ',', '.')) if espessura_text and espessura_text.strip() != '' else 0
        raio_interno = float(raio_interno_str.replace(
            ',', '.')) if raio_interno_str and raio_interno_str.strip() != '' else 0
        deducao_espec = float(deducao_espec_str.replace(
            ',', '.')) if deducao_espec_str.strip() else 0

        # Obtém dedução padrão do label
        deducao_label_text = verificar_widget_inicializado(
            g.DED_LBL, 'text', '0') or '0'
        deducao_valor = float(deducao_label_text.replace(
            ',', '.')) if deducao_label_text else 0

        # Valida se os valores necessários são válidos
        if raio_interno <= 0 or espessura <= 0:
            # Limpar labels se valores inválidos
            if g.K_LBL and hasattr(g.K_LBL, 'setText'):
                g.K_LBL.setText('')
            if g.OFFSET_LBL and hasattr(g.OFFSET_LBL, 'setText'):
                g.OFFSET_LBL.setText('')
            return

        # Determina qual dedução usar
        deducao_usada = deducao_espec if deducao_espec > 0 else deducao_valor
        usa_deducao_especifica = deducao_espec > 0

        # Calcula a razão raio/espessura
        razao_re = raio_interno / espessura

        # Sempre usa a fórmula personalizada quando há dedução disponível
        if deducao_usada > 0:
            # Fórmula corrigida para fator K quando dedução é fornecida
            fator_k = (4 * (espessura - (deducao_usada / 2) +
                       raio_interno) - (pi * raio_interno)) / (pi * espessura)

            # Limita o fator K a valores razoáveis
            fator_k = max(0.0, min(fator_k, 0.5))
        else:
            # Usa tabela de referência baseada na razão raio/espessura quando não há dedução
            fator_k = obter_fator_k_da_tabela(razao_re)

        # Calcula o offset
        offset = fator_k * espessura

        # Atualiza os labels com os valores calculados
        if g.K_LBL and hasattr(g.K_LBL, 'setText'):
            g.K_LBL.setText(f"{fator_k:.2f}")
            # Aplica cor diferente se usando dedução específica
            if hasattr(g.K_LBL, 'setStyleSheet'):
                if usa_deducao_especifica:
                    g.K_LBL.setStyleSheet("color: blue")
                else:
                    g.K_LBL.setStyleSheet("")

        if g.OFFSET_LBL and hasattr(g.OFFSET_LBL, 'setText'):
            g.OFFSET_LBL.setText(f"{offset:.2f}")
            # Aplica cor diferente se usando dedução específica
            if hasattr(g.OFFSET_LBL, 'setStyleSheet'):
                if usa_deducao_especifica:
                    g.OFFSET_LBL.setStyleSheet("color: blue")
                else:
                    g.OFFSET_LBL.setStyleSheet("")

    except ValueError as e:
        print(f"Erro ao converter valores para o cálculo do fator K: {e}")
        # Limpar labels em caso de erro
        if g.K_LBL and hasattr(g.K_LBL, 'setText'):
            g.K_LBL.setText('N/A')
            if hasattr(g.K_LBL, 'setStyleSheet'):
                g.K_LBL.setStyleSheet("color: red")
        if g.OFFSET_LBL and hasattr(g.OFFSET_LBL, 'setText'):
            g.OFFSET_LBL.setText('N/A')
            if hasattr(g.OFFSET_LBL, 'setStyleSheet'):
                g.OFFSET_LBL.setStyleSheet("color: red")
    except (AttributeError, TypeError) as e:
        print(f"Erro de atributo ou tipo no cálculo do fator K: {e}")


def obter_fator_k_da_tabela(razao_re):
    """
    Obtém o fator K da tabela de referência baseado na razão raio/espessura.
    Usa interpolação linear para valores intermediários.

    Args:
        razao_re (float): Razão entre raio interno e espessura

    Returns:
        float: Fator K correspondente
    """
    # Limita a razão aos valores da tabela
    razao_re = max(0.1, min(razao_re, 10.0))

    # Se o valor está exatamente na tabela, retorna diretamente
    if razao_re in g.RAIO_K:
        return g.RAIO_K[razao_re]

    # Encontra os valores adjacentes para interpolação
    razoes_ordenadas = sorted(g.RAIO_K.keys())

    for i in range(len(razoes_ordenadas) - 1):
        r1 = razoes_ordenadas[i]
        r2 = razoes_ordenadas[i + 1]

        if r1 <= razao_re <= r2:
            # Interpolação linear
            k1 = g.RAIO_K[r1]
            k2 = g.RAIO_K[r2]
            fator_k = k1 + (k2 - k1) * (razao_re - r1) / (r2 - r1)
            return fator_k

    # Se não encontrou na interpolação, usa o valor mais próximo
    if razao_re < razoes_ordenadas[0]:
        return g.RAIO_K[razoes_ordenadas[0]]
    else:
        return g.RAIO_K[razoes_ordenadas[-1]]


def aba_minima_externa():
    """
    Calcula a aba mínima externa com base no valor do canal e na espessura.
    Fórmula: Aba mínima = (Largura do canal / 2) + Espessura + Margem de segurança
    Atualiza o label correspondente com o valor calculado.
    """
    aba_minima_valor = 0  # Valor padrão caso a condição não seja satisfeita

    try:
        canal_valor = verificar_widget_inicializado(
            g.CANAL_COMB, 'currentText', '')
        if canal_valor != "":
            # Extrai o valor numérico do canal (pode estar em formato "25mm" ou "V=25")
            numeros = re.findall(r'\d+\.?\d*', canal_valor)
            if numeros:
                canal_valor_num = float(numeros[0])
                espessura_text = verificar_widget_inicializado(
                    g.ESP_COMB, 'currentText', '0')
                espessura = float(espessura_text.replace(',', '.'))

                # Fórmula para aba mínima: metade da largura do canal + espessura + margem
                aba_minima_valor = canal_valor_num / 2 + espessura + 2

                if g.ABA_EXT_LBL and hasattr(g.ABA_EXT_LBL, 'setText'):
                    g.ABA_EXT_LBL.setText(f"{aba_minima_valor:.0f}")
                    if hasattr(g.ABA_EXT_LBL, 'setStyleSheet'):
                        g.ABA_EXT_LBL.setStyleSheet("")
            else:
                if g.ABA_EXT_LBL and hasattr(g.ABA_EXT_LBL, 'setText'):
                    g.ABA_EXT_LBL.setText("N/A")
                    if hasattr(g.ABA_EXT_LBL, 'setStyleSheet'):
                        g.ABA_EXT_LBL.setStyleSheet("color: red")
        else:
            # Limpar label se não houver canal selecionado
            if g.ABA_EXT_LBL and hasattr(g.ABA_EXT_LBL, 'setText'):
                g.ABA_EXT_LBL.setText("")

    except (ValueError, AttributeError) as e:
        print(f"Erro ao calcular aba mínima externa: {e}")
        if g.ABA_EXT_LBL and hasattr(g.ABA_EXT_LBL, 'setText'):
            g.ABA_EXT_LBL.setText("N/A")
            if hasattr(g.ABA_EXT_LBL, 'setStyleSheet'):
                g.ABA_EXT_LBL.setStyleSheet("color: red")

    return aba_minima_valor


def z_minimo_externo():
    """
    Calcula o valor mínimo externo Z com base na espessura, dedução e largura do canal.
    Fórmula: Z mínimo = Espessura + (Dedução / 2) + (Largura do canal / 2) + Margem
    Atualiza o label correspondente com o valor calculado.
    """
    try:
        # Obtém os valores dos widgets e valida
        material = verificar_widget_inicializado(g.MAT_COMB, 'currentText', '')
        espessura_text = verificar_widget_inicializado(
            g.ESP_COMB, 'currentText', '0')
        canal_valor = verificar_widget_inicializado(
            g.CANAL_COMB, 'currentText', '')

        # Converte espessura
        espessura = float(espessura_text.replace(',', '.'))

        # Obtém dedução do label
        deducao_label_text = verificar_widget_inicializado(
            g.DED_LBL, 'text', '0')
        deducao_valor = float(deducao_label_text.replace(
            ',', '.')) if deducao_label_text else 0

        # Verifica se todos os valores necessários estão disponíveis
        if not material or not canal_valor or espessura <= 0:
            if g.Z_EXT_LBL and hasattr(g.Z_EXT_LBL, 'setText'):
                g.Z_EXT_LBL.setText("")
            return

        # Busca o canal no banco de dados
        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

        if canal_obj is None:
            if g.Z_EXT_LBL and hasattr(g.Z_EXT_LBL, 'setText'):
                g.Z_EXT_LBL.setText("N/A")
                if hasattr(g.Z_EXT_LBL, 'setStyleSheet'):
                    g.Z_EXT_LBL.setStyleSheet("color: red")
            return

        # Verifica se o canal tem largura definida
        try:
            largura_canal = canal_obj.largura
            if largura_canal is None:
                if g.Z_EXT_LBL and hasattr(g.Z_EXT_LBL, 'setText'):
                    g.Z_EXT_LBL.setText("N/A")
                    if hasattr(g.Z_EXT_LBL, 'setStyleSheet'):
                        g.Z_EXT_LBL.setStyleSheet("color: red")
                return
        except (AttributeError, ValueError, TypeError):
            if g.Z_EXT_LBL and hasattr(g.Z_EXT_LBL, 'setText'):
                g.Z_EXT_LBL.setText("N/A")
                if hasattr(g.Z_EXT_LBL, 'setStyleSheet'):
                    g.Z_EXT_LBL.setStyleSheet("color: red")
            return

        # Calcula o Z mínimo externo
        if deducao_valor > 0:
            # Fórmula: Espessura + (Dedução / 2) + (Largura do canal / 2) + Margem
            valor_z_min_ext = espessura + \
                (deducao_valor / 2) + (largura_canal / 2) + 2

            if g.Z_EXT_LBL and hasattr(g.Z_EXT_LBL, 'setText'):
                g.Z_EXT_LBL.setText(f'{valor_z_min_ext:.0f}')
                if hasattr(g.Z_EXT_LBL, 'setStyleSheet'):
                    g.Z_EXT_LBL.setStyleSheet("")
        else:
            # Sem dedução disponível
            if g.Z_EXT_LBL and hasattr(g.Z_EXT_LBL, 'setText'):
                g.Z_EXT_LBL.setText("N/A")
                if hasattr(g.Z_EXT_LBL, 'setStyleSheet'):
                    g.Z_EXT_LBL.setStyleSheet("color: orange")

    except ValueError as e:
        print(
            f"Erro ao converter valores para o cálculo do Z mínimo externo: {e}")
        if g.Z_EXT_LBL and hasattr(g.Z_EXT_LBL, 'setText'):
            g.Z_EXT_LBL.setText("N/A")
            if hasattr(g.Z_EXT_LBL, 'setStyleSheet'):
                g.Z_EXT_LBL.setStyleSheet("color: red")
    except (AttributeError, TypeError) as e:
        print(f"Erro de atributo ou tipo no cálculo do Z mínimo externo: {e}")


def _obter_valores_dobras(w):
    """Obtém os valores das dobras dos widgets de entrada para uma coluna específica."""
    return [
        getattr(g, f'aba{i}_entry_{w}').text() or ''
        if getattr(g, f'aba{i}_entry_{w}', None) is not None else ''
        for i in range(1, g.N)
    ]


def _obter_valor_deducao():
    """Obtém o valor da dedução dos widgets correspondentes."""
    deducao_valor = str(verificar_widget_inicializado(g.DED_LBL, 'text', '')).replace(
        ' Copiado!', '')
    deducao_espec_str = verificar_widget_inicializado(
        g.DED_ESPEC_ENTRY, 'text', '') or ''
    deducao_espec = deducao_espec_str.replace(',', '.')

    if deducao_espec != "":
        return deducao_espec
    return deducao_valor


def _calcular_medida_dobra(dobra, deducao_valor, i, valores_dobras):
    """Calcula a medida da dobra baseada na posição e valor de dedução."""
    # Encontrar as posições das abas com valores (primeira e última)
    posicoes_com_valores = []
    for idx, valor in enumerate(valores_dobras):
        if valor.strip():  # Se não está vazio
            # Converter para índice baseado em 1
            posicoes_com_valores.append(idx + 1)

    if len(posicoes_com_valores) == 0:
        return float(dobra) - float(deducao_valor) / 2

    primeira_posicao = posicoes_com_valores[0]
    ultima_posicao = posicoes_com_valores[-1]

    # Aplicar lógica baseada na posição
    if i == primeira_posicao or i == ultima_posicao:
        # Primeira ou última aba com valor usa dedução/2
        resultado = float(dobra) - float(deducao_valor) / 2
    else:
        # Abas intermediárias usam dedução completa
        resultado = float(dobra) - float(deducao_valor)

    return resultado


def _atualizar_widgets_dobra(i, w, medidadobra, metade_dobra):
    """Atualiza os widgets com os valores calculados de dobra."""
    def atualizar_widget_seguro(widget, valor):
        """Atualiza um widget de forma segura"""
        if widget is not None and hasattr(widget, 'setText'):
            widget.setText(f"{valor:.2f}")
            if hasattr(widget, 'setStyleSheet'):
                widget.setStyleSheet("")

    widget_medida = getattr(g, f'medidadobra{i}_label_{w}', None)
    widget_metade = getattr(g, f'metadedobra{i}_label_{w}', None)

    atualizar_widget_seguro(widget_medida, medidadobra)
    atualizar_widget_seguro(widget_metade, metade_dobra)


def _limpar_widgets_dobra(i, w):
    """Limpa os widgets de dobra quando o valor está vazio."""
    def limpar_widget_seguro(widget):
        """Limpa um widget de forma segura"""
        if widget is not None and hasattr(widget, 'setText'):
            widget.setText("")

    widget_medida = getattr(g, f'medidadobra{i}_label_{w}', None)
    widget_metade = getattr(g, f'metadedobra{i}_label_{w}', None)

    limpar_widget_seguro(widget_medida)
    limpar_widget_seguro(widget_metade)


def _calcular_e_atualizar_blank(w):
    """Calcula e atualiza os valores de blank para uma coluna."""
    blank = sum(
        float(getattr(g, f'medidadobra{row}_label_{w}').text().replace(
            ' Copiado!', ''))
        for row in range(1, g.N)
        if getattr(g, f'medidadobra{row}_label_{w}', None) is not None
        and hasattr(getattr(g, f'medidadobra{row}_label_{w}'), 'text')
        and getattr(g, f'medidadobra{row}_label_{w}').text()
    )

    metade_blank = blank / 2

    # Atualizar os widgets com os valores calculados
    label = getattr(g, f'medida_blank_label_{w}', None)
    if label and hasattr(label, 'setText'):
        if blank:
            label.setText(f"{blank:.2f}")
            if hasattr(label, 'setStyleSheet'):
                label.setStyleSheet("")
        else:
            label.setText("")

    label = getattr(g, f'metade_blank_label_{w}', None)
    if label and hasattr(label, 'setText'):
        if metade_blank:
            label.setText(f"{metade_blank:.2f}")
            if hasattr(label, 'setStyleSheet'):
                label.setStyleSheet("")
        else:
            label.setText("")


def calcular_dobra(w):
    """
    Calcula as medidas de dobra e metade de dobra com base nos valores de entrada.
    """
    # Obter valores das dobras diretamente dos widgets para a coluna específica
    valores_dobras = _obter_valores_dobras(w)

    # Obter valor da dedução
    deducao_valor = _obter_valor_deducao()

    if not deducao_valor:
        return

    # Iterar pelas linhas para calcular as medidas
    for i in range(1, g.N):
        # Índice na lista valores_dobras (base 0)
        indice_lista = i - 1

        if indice_lista >= len(valores_dobras):
            continue

        dobra = valores_dobras[indice_lista].replace(',', '.')

        if dobra == "":
            _limpar_widgets_dobra(i, w)
        else:
            medidadobra = _calcular_medida_dobra(
                dobra, deducao_valor, i, valores_dobras)
            metade_dobra = medidadobra / 2
            _atualizar_widgets_dobra(i, w, medidadobra, metade_dobra)

        # Verificar aba mínima usando o valor atual
        valor_atual = valores_dobras[indice_lista] if indice_lista < len(
            valores_dobras) else ""
        verificar_aba_minima(valor_atual, i, w)

    # Calcular e atualizar blank para esta coluna (fora do loop)
    _calcular_e_atualizar_blank(w)


def verificar_aba_minima(dobra, i, w):
    """
    Verifica se a dobra é menor que a aba mínima e atualiza o widget correspondente.
    """
    # Verificar se a dobra é menor que a aba mínima
    aba_minima = aba_minima_externa()

    # Obter o widget dinamicamente
    entry_widget = getattr(g, f'aba{i}_entry_{w}', None)

    if entry_widget is None:
        return

    # Verificar se o campo está vazio
    if not dobra.strip():  # Se o campo estiver vazio ou contiver apenas espaços
        if hasattr(entry_widget, 'setStyleSheet'):
            entry_widget.setStyleSheet("")
    else:
        try:
            # Converter o valor de 'dobra' para float e verificar se é menor que 'aba_minima'
            if float(dobra) < aba_minima:
                if hasattr(entry_widget, 'setStyleSheet'):
                    entry_widget.setStyleSheet(
                        "color: white; background-color: red")
            else:
                if hasattr(entry_widget, 'setStyleSheet'):
                    entry_widget.setStyleSheet("")
        except ValueError:
            # Tratar erros de conversão
            if hasattr(entry_widget, 'setStyleSheet'):
                entry_widget.setStyleSheet("")
            print(f"Erro: Valor inválido na aba {i}, coluna {w}.")


def razao_ri_espessura():
    """
    Calcula a razão entre o raio interno e a espessura, atualizando o label correspondente.
    Esta razão é importante para determinar o fator K adequado para cálculos de dobra.
    """
    # Verifica se o widget existe
    if not g.RAZAO_RIE_LBL or not hasattr(g.RAZAO_RIE_LBL, 'setText'):
        return

    try:
        # Obtém os valores dos widgets e valida
        espessura_text = verificar_widget_inicializado(
            g.ESP_COMB, 'currentText', '0') or '0'
        espessura = float(espessura_text.replace(',', '.'))

        raio_interno_str = verificar_widget_inicializado(
            g.RI_ENTRY, 'text', '0') or '0'
        raio_interno = float(raio_interno_str.replace(',', '.'))

        # Valida se os valores necessários são maiores que zero
        if raio_interno <= 0 or espessura <= 0:
            g.RAZAO_RIE_LBL.setText('')
            return

        # Calcula a razão
        razao = raio_interno / espessura

        # Limita a razão a valores razoáveis (conforme tabela de referência)
        razao = min(razao, 10.0)

        # Atualiza o label com o valor calculado
        g.RAZAO_RIE_LBL.setText(f"{razao:.1f}")

        # Aplica cor baseada na faixa de valores
        if hasattr(g.RAZAO_RIE_LBL, 'setStyleSheet'):
            if razao < 0.5:
                g.RAZAO_RIE_LBL.setStyleSheet(
                    "color: red")  # Razão muito baixa
            elif razao > 5.0:
                g.RAZAO_RIE_LBL.setStyleSheet("color: orange")  # Razão alta
            else:
                g.RAZAO_RIE_LBL.setStyleSheet("")  # Faixa normal - cor padrão

    except ValueError as e:
        print(f"Erro ao converter valores para o cálculo da razão: {e}")
        g.RAZAO_RIE_LBL.setText('N/A')
        if hasattr(g.RAZAO_RIE_LBL, 'setStyleSheet'):
            g.RAZAO_RIE_LBL.setStyleSheet("color: red")
    except (AttributeError, TypeError) as e:
        print(
            f"Erro de atributo ou tipo no cálculo da razão ri/espessura: {e}")
