from PIL import Image
import os

# Caminho do arquivo PNG
png_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icone.png')

# Caminho de saída para o arquivo ICO
ico_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icone.ico')

# Converter PNG para ICO
img = Image.open(png_path)
img.save(ico_path, format='ICO', sizes=[(32, 32)])  # Define o tamanho do ícone
print(f"Ícone convertido e salvo em: {ico_path}")