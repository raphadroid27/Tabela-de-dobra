import ezdxf
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Carregar o arquivo DXF
doc = ezdxf.readfile("c:/Users/Luma/Desktop/Drawing3.dxf")
msp = doc.modelspace()

# Listas para armazenar coordenadas dos vetores
lines = []
arcs = []

# Iterar sobre as entidades no espaço do modelo
for entity in msp:
    if entity.dxftype() == 'LINE':
        start = entity.dxf.start
        end = entity.dxf.end
        lines.append((start, end))
    elif entity.dxftype() == 'ARC':
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle
        arcs.append((center, radius, start_angle, end_angle))

# Plotar as linhas
for line in lines:
    start, end = line
    plt.plot([start.x, end.x], [start.y, end.y], 'b-')

# Plotar os arcos
for arc in arcs:
    center, radius, start_angle, end_angle = arc
    arc_patch = patches.Arc(center, 2*radius, 2*radius, angle=0, theta1=start_angle, theta2=end_angle, color='b')
    plt.gca().add_patch(arc_patch)

# Configurar o gráfico
plt.gca().set_aspect('equal', adjustable='box')
plt.xlabel('X')
plt.ylabel('Y')
plt.title('Plotagem de Vetores do Arquivo DXF')
plt.grid(True)

# Mostrar o gráfico
plt.show()