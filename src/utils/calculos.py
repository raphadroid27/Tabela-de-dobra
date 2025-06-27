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
        metodo: O método a ser chamado ('get', 'cget', 'config')
        default_value: Valor padrão caso o widget não esteja inicializado

    Returns:
        O resultado do método ou o valor padrão
    """
    if widget is None:
        return default_value

    try:
        if metodo == 'get':
            return widget.get()
        if metodo == 'cget':
            return widget.cget('text')
        if metodo == 'config':
            return widget.config
        return default_value
    except (AttributeError, TypeError):
        return default_value

def calcular_k_offset():
    """
    Calcula o fator K com base nos valores de espessura, dedução e raio interno.
    Atualiza o label correspondente com o valor calculado.
    """
    try:
        # Obtém os valores diretamente e verifica se são válidos
        espessura = float(verificar_widget_inicializado(g.ESP_COMB, 'get', '0') or 0)
        raio_interno_str = verificar_widget_inicializado(g.RI_ENTRY, 'get', '0') or '0'
        raio_interno = float(raio_interno_str.replace(',', '.'))
        deducao_espec_str = verificar_widget_inicializado(g.DED_ESPEC_ENTRY, 'get', '0') or '0'
        deducao_espec = float(deducao_espec_str.replace(',', '.'))
        deducao_valor = float(verificar_widget_inicializado(g.DED_LBL, 'cget', '0') or 0)

        # Usa a dedução específica, se fornecida
        if verificar_widget_inicializado(g.DED_ESPEC_ENTRY, 'get'):
            deducao_valor = deducao_espec

        # Valida se os valores necessários são maiores que zero
        if not raio_interno or not espessura or not deducao_valor:
            return

        # Calcula o fator K
        fator_k = (4 * (espessura - (deducao_valor / 2) + raio_interno) -
                     (pi * raio_interno)) / (pi * espessura)

        # Limita o fator K a 0.5
        fator_k = min(fator_k, 0.5)

        # Calcula o offset
        offset = fator_k * espessura

        # Atualiza o label com o valor calculado
        if g.K_LBL is not None:
            g.K_LBL.config(text=f"{fator_k:.2f}", fg="blue"
                           if deducao_valor == deducao_espec else "black")

        if g.OFFSET_LBL is not None:
            g.OFFSET_LBL.config(text=f"{offset:.2f}", fg="blue"
                                if deducao_valor == deducao_espec else "black")

    except ValueError:
        # Trata erros de conversão
        print("Erro: Valores inválidos fornecidos para o cálculo do fator K.")

def aba_minima_externa():
    """
    Calcula a aba mínima externa com base no valor do canal e na espessura.
    Atualiza o label correspondente com o valor calculado.
    """
    aba_minima_valor = 0  # Valor padrão caso a condição não seja satisfeita

    try:
        canal_valor = verificar_widget_inicializado(g.CANAL_COMB, 'get', '')
        if canal_valor != "":
            canal_valor = float(re.findall(r'\d+\.?\d*', canal_valor)[0])
            espessura = float(verificar_widget_inicializado(g.ESP_COMB, 'get', '0'))

            aba_minima_valor = canal_valor / 2 + espessura + 2
            if g.ABA_EXT_LBL is not None:
                g.ABA_EXT_LBL.config(text=f"{aba_minima_valor:.0f}")
    except (ValueError, AttributeError) as e:
        print(f"Erro ao calcular aba mínima externa: {e}")
        if g.ABA_EXT_LBL is not None:
            g.ABA_EXT_LBL.config(text="N/A", fg="red")

    return aba_minima_valor

def z_minimo_externo():
    """
    Calcula o valor mínimo externo com base na espessura, dedução e largura do canal.
    Atualiza o label correspondente com o valor calculado.
    """
    try:
        # Obtém os valores diretamente e verifica se são válidos
        material = verificar_widget_inicializado(g.MAT_COMB, 'get', '')
        espessura = float(verificar_widget_inicializado(g.ESP_COMB, 'get', '0'))
        canal_valor = verificar_widget_inicializado(g.CANAL_COMB, 'get', '')
        deducao_valor = float(verificar_widget_inicializado(g.DED_LBL, 'cget', '0'))

        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

        if material != "" and espessura != "" and canal_valor != "":
            if canal_obj is None or not hasattr(canal_obj, 'largura'):
                if g.Z_EXT_LBL is not None:
                    g.Z_EXT_LBL.config(text="N/A", fg="red")
                return
              # Verificar se largura tem valor válido
            try:
                largura_value = canal_obj.largura
                # Converter para valor Python para comparação
                if largura_value is None:
                    if g.Z_EXT_LBL is not None:
                        g.Z_EXT_LBL.config(text="N/A", fg="red")
                    return
            except (AttributeError, ValueError, TypeError):
                if g.Z_EXT_LBL is not None:
                    g.Z_EXT_LBL.config(text="N/A", fg="red")
                return

            if canal_valor and deducao_valor:
                canal_valor = float(re.findall(r'\d+\.?\d*', canal_valor)[0])
                valor_z_min_ext = espessura + (deducao_valor / 2) + (canal_obj.largura / 2) + 2
                if g.Z_EXT_LBL is not None:
                    g.Z_EXT_LBL.config(text=f'{valor_z_min_ext:.0f}', fg="black")

    except ValueError:
        # Trata erros de conversão
        print("Erro: Valores inválidos fornecidos para o cálculo do Z mínimo externo.")

def _obter_valores_dobras(w):
    """Obtém os valores das dobras dos widgets de entrada."""
    return [
        [
            getattr(g, f'aba{i}_entry_{col}').get() or ''
            if getattr(g, f'aba{i}_entry_{col}', None) is not None else ''
            for col in range(1, w + 1)
        ]
        for i in range(1, g.N)
    ]

def _obter_valor_deducao():
    """Obtém o valor da dedução dos widgets correspondentes."""
    deducao_valor = str(verificar_widget_inicializado(g.DED_LBL, 'cget', '')).replace(
        ' Copiado!', '')
    deducao_espec_str = verificar_widget_inicializado(g.DED_ESPEC_ENTRY, 'get', '') or ''
    deducao_espec = deducao_espec_str.replace(',', '.')

    if deducao_espec != "":
        return deducao_espec
    return deducao_valor

def _calcular_medida_dobra(dobra, deducao_valor, i):
    """Calcula a medida da dobra baseada na posição e valor de dedução."""
    if i in (1, g.N - 1):
        return float(dobra) - float(deducao_valor) / 2

    if (g.DOBRAS_VALORES is None or len(g.DOBRAS_VALORES) <= i or
        len(g.DOBRAS_VALORES[i]) <= 0 or
        not g.DOBRAS_VALORES[i][0]):
        return float(dobra) - float(deducao_valor) / 2

    return float(dobra) - float(deducao_valor)

def _atualizar_widgets_dobra(i, w, medidadobra, metade_dobra):
    """Atualiza os widgets com os valores calculados de dobra."""
    widget_medida = getattr(g, f'medidadobra{i}_label_{w}', None)
    widget_metade = getattr(g, f'metadedobra{i}_label_{w}', None)
    if widget_medida is not None:
        widget_medida.config(text=f'{medidadobra:.2f}', fg="black")
    if widget_metade is not None:
        widget_metade.config(text=f'{metade_dobra:.2f}', fg="black")

def _limpar_widgets_dobra(i, w):
    """Limpa os widgets de dobra quando o valor está vazio."""
    widget_medida = getattr(g, f'medidadobra{i}_label_{w}', None)
    widget_metade = getattr(g, f'metadedobra{i}_label_{w}', None)
    if widget_medida is not None:
        widget_medida.config(text="")
    if widget_metade is not None:
        widget_metade.config(text="")

def _calcular_e_atualizar_blank(w):
    """Calcula e atualiza os valores de blank para uma coluna."""
    blank = sum(
        float(getattr(g, f'medidadobra{row}_label_{w}').cget('text').replace(' Copiado!', ''))
        for row in range(1, g.N)
        if getattr(g, f'medidadobra{row}_label_{w}').cget('text')
    )

    metade_blank = blank / 2

    # Atualizar os widgets com os valores calculados
    label = getattr(g, f'medida_blank_label_{w}')
    if blank:
        label.config(text=f"{blank:.2f}", fg="black")
    else:
        label.config(text="")

    label = getattr(g, f'metade_blank_label_{w}')
    if metade_blank:
        label.config(text=f"{metade_blank:.2f}", fg="black")
    else:
        label.config(text="")

def calcular_dobra(w):
    """
    Calcula as medidas de dobra e metade de dobra com base nos valores de entrada.
    """
    # Obter valores das dobras
    g.DOBRAS_VALORES = _obter_valores_dobras(w)

    # Exibir a matriz de valores para depuração
    print("Matriz de dobras (g.dobras_get):")
    if g.DOBRAS_VALORES is not None:
        for linha in g.DOBRAS_VALORES:
            print(linha)

    # Obter valor da dedução
    deducao_valor = _obter_valor_deducao()

    if not deducao_valor:
        return

    # Iterar pelas linhas e colunas para calcular as medidas
    for i in range(1, g.N):
        for col in range(1, w + 1):
            if (g.DOBRAS_VALORES is None or len(g.DOBRAS_VALORES) <= i - 1 or
                len(g.DOBRAS_VALORES[i - 1]) <= col - 1):
                continue

            dobra = g.DOBRAS_VALORES[i - 1][col - 1].replace(',', '.')

            if dobra == "":
                _limpar_widgets_dobra(i, col)
            else:
                medidadobra = _calcular_medida_dobra(dobra, deducao_valor, i)
                metade_dobra = medidadobra / 2
                _atualizar_widgets_dobra(i, col, medidadobra, metade_dobra)

            _calcular_e_atualizar_blank(col)
            verificar_aba_minima(g.DOBRAS_VALORES[i - 1][col - 1], i, col)

def verificar_aba_minima(dobra, i, w):
    """
    Verifica se a dobra é menor que a aba mínima e atualiza o widget correspondente.
    """
    # Verificar se a dobra é menor que a aba mínima
    aba_minima = aba_minima_externa()

    # Obter o widget dinamicamente
    entry_widget = getattr(g, f'aba{i}_entry_{w}')

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

def razao_ri_espessura():
    """
    Calcula a razão entre o raio interno e a espessura, atualizando o label correspondente.
    """
    if not g.RAZAO_RIE_LBL or not g.RAZAO_RIE_LBL.winfo_exists():
        return

    try:
        # Obtém os valores diretamente e verifica se são válidos
        espessura = float(verificar_widget_inicializado(g.ESP_COMB, 'get', '0') or 0)
        raio_interno_str = verificar_widget_inicializado(g.RI_ENTRY, 'get', '0') or '0'
        raio_interno = float(raio_interno_str.replace(',', '.'))

        # Valida se os valores necessários são maiores que zero
        if not raio_interno or not espessura:
            return

        # Calcula a razão
        razao = raio_interno / espessura

        razao = min(razao, 10)

        # Atualiza o label com o valor calculado
        g.RAZAO_RIE_LBL.config(text=f"{razao:.1f}")

    except ValueError:
        # Trata erros de conversão
        print("Erro: Valores inválidos fornecidos para o cálculo da razão.")
