import os
import requests
import zipfile

# ===== CONFIGURAÇÃO =====
YEARS = [2020, 2021, 2022, 2023, 2024]
BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"
OUTPUT_DIR = "data_raw"

def download_file(url, output_path):
    print(f"Baixando: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Arquivo salvo em: {output_path}")
        
        # Extrair automaticamente o ZIP
        extract_dir = os.path.splitext(output_path)[0]
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(output_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        print(f"Arquivos extraídos em: {extract_dir}")        
    else:
        print(f"Erro ao baixar {url} - Status code: {response.status_code}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for year in YEARS:
        filename = f"dfp_cia_aberta_{year}.zip"
        url = BASE_URL + filename
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        download_file(url, output_path)

if __name__ == "__main__":
    main()