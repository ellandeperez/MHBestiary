import requests
import json
from time import sleep

def get_monster_materials(monster_name):
    """Obtiene materiales desde la base de datos de MHWorld"""
    try:
        # URL del archivo raw de GitHub con los datos
        db_url = "https://raw.githubusercontent.com/gatheringhallstudios/MHWorldData/master/mhdata/data/rewards.json"
        print(f"Obteniendo datos para {monster_name}...")
        
        response = requests.get(db_url)
        if response.status_code == 200:
            all_materials = response.json()
            monster_materials = []
            
            # Buscar materiales del monstruo específico
            for material in all_materials:
                if monster_name.lower() in material['monster'].lower():
                    material_data = {
                        "name": material['item_en'],
                        "rarity": material.get('rarity', 6),
                        "dropRate": material.get('percentage', 10),
                        "source": material.get('condition_en', 'Reward'),
                        "icon": "https://github.com/ellandeperez/MHBestiary/blob/main/MHImages/Icons/particons/m_scale.png?raw=true"
                    }
                    monster_materials.append(material_data)
            
            if monster_materials:
                print(f"Encontrados {len(monster_materials)} materiales")
                return monster_materials
            
            print(f"No se encontraron materiales para {monster_name}")
            return None
            
        print(f"Error accediendo a la base de datos: {response.status_code}")
        return None
            
    except Exception as e:
        print(f"Error obteniendo materiales: {str(e)}")
        return None

# ...resto del código se mantiene igual...

# El resto del código se mantiene igual...

def update_monster_materials():
    """Actualiza los materiales en monstruos.json"""
    try:
        print("Iniciando actualización de materiales...")
        
        with open('monstruos.json', 'r', encoding='utf-8') as f:
            monsters = json.load(f)
        
        updated_count = 0
        for monster in monsters:
            print(f"\nProcesando {monster['name']}...")
            materials = get_monster_materials(monster['name'])
            
            if materials:
                monster['materials'] = materials
                updated_count += 1
                print(f"✓ Actualizado {monster['name']}")
            else:
                print(f"✗ No se pudieron obtener materiales para {monster['name']}")
            
            sleep(2)  # Incrementado el delay para evitar bloqueos
        
        # Guarda los cambios
        with open('monstruos.json', 'w', encoding='utf-8') as f:
            json.dump(monsters, f, ensure_ascii=False, indent=2)
            
        print(f"\nProceso completado. Actualizados {updated_count} de {len(monsters)} monstruos")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    update_monster_materials()