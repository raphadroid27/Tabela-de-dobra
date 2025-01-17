from math import pi

def calcular_dobra_ang():
    distancia = 12
    angulo = 90
    raio = 1
    offset = 0.2732
    dobra = distancia + (angulo*(raio + offset)*pi/360)

    print(f'Essa é a dobra: {dobra:.1f}')

calcular_dobra_ang()