import requests
import os
import json

def download_database(url, filename):
    """Descarga una base de datos desde GitHub"""
    print(f"Descargando {filename}...")
    response = requests.get(url)
    if response.status_code == 200:
        with open(f"databases/{filename}", 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)
        print(f"✓ {filename} descargado correctamente")
    else:
        print(f"✗ Error descargando {filename}")

def setup_databases():
    """Descarga todas las bases de datos necesarias"""
    # Crear directorio si no existe
    if not os.path.exists('databases'):
        os.makedirs('databases')

    # URLs de las bases de datos
    databases = {
        'mhworld_monsters.json': 'https://raw.githubusercontent.com/gatheringhallstudios/MHWorldData/master/mhdata/data/monsters.json',
        'mhworld_items.json': 'https://raw.githubusercontent.com/gatheringhallstudios/MHWorldData/master/mhdata/data/items.json',
        'mhworld_rewards.json': 'https://raw.githubusercontent.com/gatheringhallstudios/MHWorldData/master/mhdata/data/rewards.json',
        'mh4u_monsters.json': 'https://raw.githubusercontent.com/gatheringhallstudios/MH4U-Database/master/app/src/main/assets/data/monsters.json',
        'mhgen_monsters.json': 'https://raw.githubusercontent.com/gatheringhallstudios/MHGenDatabase/master/app/src/main/assets/data/monsters.json'
    }

    for filename, url in databases.items():
        download_database(url, filename)

if __name__ == "__main__":
    setup_databases()