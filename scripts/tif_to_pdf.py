from PIL import Image
import os

# Caminho da pasta com os arquivos .tif
pasta_origem = "Y:\\MULTIVAC BRASIL - MACSUEL\\157836-24\\PC 65553"
pasta_destino = "Y:\\MULTIVAC BRASIL - MACSUEL\\157836-24\\PC 65553"

# Certifique-se de que a pasta de destino existe
os.makedirs(pasta_destino, exist_ok=True)

# Loop pelos arquivos na pasta
for arquivo in os.listdir(pasta_origem):
    if arquivo.lower().endswith(".tif"):
        caminho_tif = os.path.join(pasta_origem, arquivo)
        nome_pdf = os.path.splitext(arquivo)[0] + ".pdf"
        caminho_pdf = os.path.join(pasta_destino, nome_pdf)

        with Image.open(caminho_tif) as img:
            img.convert("RGB").save(caminho_pdf, "PDF")

        print(f"Convertido: {arquivo} → {nome_pdf}")
