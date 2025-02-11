import pandas as pd
import json

# Cargar los CSV
monster_base = pd.read_csv("C:/Users/eperez/Desktop/Tonterias/MHProyecto/monster_base.csv")
monster_translations = pd.read_csv("C:/Users/eperez/Desktop/Tonterias/MHProyecto/monster_base_translations.csv")
monster_habitats = pd.read_csv("C:/Users/eperez/Desktop/Tonterias/MHProyecto/monster_habitats.csv")
monster_hitzones = pd.read_csv("C:/Users/eperez/Desktop/Tonterias/MHProyecto/monster_hitzones.csv")
monster_rewards = pd.read_csv("C:/Users/eperez/Desktop/Tonterias/MHProyecto/monster_rewards.csv")
monster_weaknesses = pd.read_csv("C:/Users/eperez/Desktop/Tonterias/MHProyecto/monster_weaknesses.csv")

# 1. Filtrar monstruos grandes y obtener nombre y tipo
large_monsters = monster_base[monster_base["size"] == "large"][["name_en", "ecology_en"]].copy()

# 2. Agregar descripción en español
large_monsters = large_monsters.merge(
    monster_translations[["name_en", "description_es"]], 
    on="name_en", 
    how="left"
)

# 3. Agregar hábitats - modificar esta sección
habitats_grouped = monster_habitats.groupby("base_name_en")["map_en"].agg(list).reset_index()
habitats_grouped["map_en"] = habitats_grouped["map_en"].apply(lambda x: list(set(x)))

large_monsters = large_monsters.merge(
    habitats_grouped,
    left_on="name_en",
    right_on="base_name_en",
    how="left"
).drop(columns=["base_name_en"])

# Reemplazar NaN con listas vacías en map_en
large_monsters["map_en"] = large_monsters["map_en"].fillna({i: [] for i in large_monsters.index})

# 4. Procesar hitzones
def convert_damage(value):
    value = float(value) if pd.notna(value) else 0
    if value <= 33:
        return 1
    elif value <= 66:
        return 2
    else:
        return 3

hitzones_processed = monster_hitzones[["base_name_en", "hitzone_en", "cut", "impact", "shot"]].copy()
# Eliminar duplicados de partes manteniendo la primera ocurrencia
hitzones_processed = hitzones_processed.drop_duplicates(subset=['base_name_en', 'hitzone_en'], keep='first')
for col in ["cut", "impact", "shot"]:
    hitzones_processed[col] = hitzones_processed[col].apply(convert_damage)

large_monsters = large_monsters.merge(
    hitzones_processed,
    left_on="name_en",
    right_on="base_name_en",
    how="left"
).drop(columns=["base_name_en"])

# 5. Procesar recompensas 
def get_rewards_for_monster(monster_name, rank="MR"):
    """Obtiene las recompensas de un monstruo para un rango específico"""
    rewards = monster_rewards[
        (monster_rewards["rank"] == rank) & 
        (monster_rewards["base_name_en"] == monster_name) &
        (~monster_rewards["condition_en"].str.contains("Guiding Lands|Investigation", case=False, na=False)) &
        (~monster_rewards["item_en"].str.contains("Tear", case=False, na=False))
    ][["base_name_en", "item_en", "percentage", "condition_en"]].copy()
    
    return rewards

def process_monster_rewards(monster_name):
    """Procesa las recompensas de un monstruo intentando diferentes rangos"""
    for rank in ["MR", "HR", "LR"]:
        rewards = get_rewards_for_monster(monster_name, rank)
        if not rewards.empty:
            return rewards
    return pd.DataFrame() # Retorna DataFrame vacío si no hay recompensas

# Obtener recompensas para cada monstruo
all_rewards = []
for monster_name in large_monsters["name_en"].unique():
    rewards = process_monster_rewards(monster_name)
    if not rewards.empty:
        all_rewards.append(rewards)

rewards_processed = pd.concat(all_rewards, ignore_index=True)
rewards_processed["percentage"] = pd.to_numeric(rewards_processed["percentage"], errors='coerce')

# Función para determinar el icono basado en el nombre del item
def get_material_icon(item_name):
    if any(x in item_name.lower() for x in ["scale", "escama"]):
        return "m_scale.png"
    elif any(x in item_name.lower() for x in ["gem", "gema", "ruby", "rubí"]):
        return "m_gem.png"
    elif any(x in item_name.lower() for x in ["plate", "placa"]):
        return "m_plate.png"
    elif any(x in item_name.lower() for x in ["horn", "cuerno"]):
        return "m_horn.png"
    elif any(x in item_name.lower() for x in ["mantle", "manto"]):
        return "m_mantle.png"
    return "m_scale.png"  # icono por defecto

# Agrupar y procesar recompensas
rewards_unique = rewards_processed.groupby(["base_name_en", "item_en"]).agg({
    "percentage": "max",
    "condition_en": lambda x: ", ".join(sorted(set(x)))
}).reset_index()

# Obtener los 3 items más raros y añadir iconos
top_rewards = (rewards_unique.sort_values(["base_name_en", "percentage"])
              .groupby("base_name_en")
              .head(3)
              .reset_index(drop=True))

# Añadir la columna de iconos
top_rewards["icon"] = top_rewards["item_en"].apply(get_material_icon)

# Añadir las recompensas al DataFrame principal
large_monsters = large_monsters.merge(
    top_rewards,
    left_on="name_en",
    right_on="base_name_en",
    how="left"
).drop(columns=["base_name_en"])

# 6. Procesar debilidades
weakness_cols = ["fire", "water", "thunder", "ice", "dragon", "poison", "sleep", "paralysis", "blast", "stun"]
weaknesses_normal = monster_weaknesses[
    (monster_weaknesses["form"] == "normal") & 
    (monster_weaknesses["name_en"].isin(large_monsters["name_en"]))
][["name_en"] + weakness_cols].copy()

large_monsters = large_monsters.merge(
    weaknesses_normal,
    on="name_en",
    how="left"
)

def find_monster_variants(name, monster_names):
    """
    Encuentra variantes de un monstruo basándose en nombres similares.
    Ejemplo: 'Glavenus' encontrará 'Acidic Glavenus'
    """
    variants = []
    base_name = name.split()[-1]  # Toma la última palabra del nombre
    
    for other_name in monster_names:
        # Si es el mismo monstruo, ignorar
        if other_name == name:
            continue
            
        # Si contiene el nombre base pero no es idéntico, es una variante
        if base_name in other_name:
            variant = {
                "name": other_name,
                "image": f"https://github.com/ellandeperez/MHBestiary/blob/main/MHImages/{other_name.replace(' ', '')}/Icon.png?raw=true"
            }
            variants.append(variant)
            
    return variants

# Procesar datos base
def process_monster_data(large_monsters):
    # Modificar el groupby para incluir map_en como lista
    agg_dict = {
        "ecology_en": "first",
        "description_es": "first",
        "map_en": "first", # mantenemos first porque ya viene como lista del merge anterior
        "hitzone_en": list,
        "cut": list,
        "impact": list,
        "shot": list,
        "fire": "first",
        "water": "first",
        "thunder": "first",
        "ice": "first",
        "dragon": "first",
        "poison": "first",
        "sleep": "first",
        "paralysis": "first",
        "blast": "first",
        "stun": "first"
    }

    # Si las columnas de recompensas existen, añadirlas al diccionario de agregación
    if "item_en" in large_monsters.columns:
        agg_dict.update({
            "item_en": list,
            "percentage": list,
            "condition_en": list,
            "icon": list
        })

    monster_groups = large_monsters.groupby("name_en").agg(agg_dict).reset_index()
    
    # Obtener lista de todos los nombres de monstruos
    all_monster_names = large_monsters["name_en"].unique().tolist()
    
    monster_list = []
    base_id = 16  # Empezar desde ID 16
    
    for _, monster in monster_groups.iterrows():
        seen_base_parts = {}
        parts = []
        
        # Mapeo de partes a nombres simplificados
        part_mapping = {
            "Head": "Head",
            "Cabeza": "Head", 
            "Tail": "Tail",
            "Cola": "Tail",
            "Wing": "Wings",
            "Wings": "Wings",
            "Alas": "Wings",
            "Body": "Body",
            "Cuerpo": "Body",
            "Torso": "Body",
            "Horn": "Horn",
            "Cuerno": "Horn",
            "Back": "Back",
            "Espalda": "Back"
        }

        # Lista de partes importantes a mantener
        important_parts = {"Head", "Tail", "Wings", "Body", "Horn", "Back"}
        
        hitzone_data = zip(
            monster["hitzone_en"],
            monster["cut"],
            monster["impact"],
            monster["shot"]
        )

        for hitzone, cut, impact, shot in hitzone_data:
            if pd.isna(hitzone):
                continue
                
            original_name = hitzone.split('(')[0].strip()
            
            # Buscar el nombre mapeado o usar el original
            base_name = None
            for key, value in part_mapping.items():
                if key.lower() in original_name.lower():
                    base_name = value
                    break
            
            # Si no es una parte importante, ignorarla
            if not base_name or base_name not in important_parts:
                continue
                
            current_stats = {
                "slash": int(cut) if pd.notna(cut) else 1,
                "blunt": int(impact) if pd.notna(impact) else 1,
                "pierce": int(shot) if pd.notna(shot) else 1
            }
            
            current_stats_sum = sum(current_stats.values())
            
            if base_name not in seen_base_parts or current_stats_sum > seen_base_parts[base_name]["total"]:
                seen_base_parts[base_name] = {
                    "total": current_stats_sum,
                    "stats": current_stats
                }
                
                part_data = {
                    "name": base_name,
                    "breakable": True,
                    "cortable": base_name == "Tail",
                    "weaknesses": current_stats
                }
                
                # Actualizar o añadir la parte
                existing_part_index = next((i for i, p in enumerate(parts) if p["name"] == base_name), None)
                if existing_part_index is not None:
                    parts[existing_part_index] = part_data
                else:
                    parts.append(part_data)

        # Procesar materiales
        materials = []
        monster_rewards = top_rewards[top_rewards["base_name_en"] == monster["name_en"]]
        
        for _, reward in monster_rewards.iterrows():
            material = {
                "name": reward["item_en"],
                "rarity": 7 if "Mantle" in reward["item_en"] else 6 if "Gem" in reward["item_en"] else 5,
                "dropRate": round(float(reward["percentage"]), 2) if pd.notna(reward["percentage"]) else 0,
                "source": reward["condition_en"],
                "icon": f"https://github.com/ellandeperez/MHBestiary/blob/main/MHImages/Icons/particons/{reward['icon']}?raw=true"
            }
            materials.append(material)

        # Encontrar variantes antes de crear monster_data
        variants = find_monster_variants(monster["name_en"], all_monster_names)
        
        monster_data = {
            "id": base_id,  # Añadir ID al principio del diccionario
            "name": monster["name_en"],
            "type": monster["ecology_en"],
            "threat": 5,
            "locale": monster["map_en"] if isinstance(monster["map_en"], list) else [],
            "variants": variants,  # Añadir las variantes encontradas
            "game": [],
            "image": f"https://github.com/ellandeperez/MHBestiary/blob/main/MHImages/{monster['name_en'].replace(' ', '')}/Icon.png?raw=true",
            "gallery": [],
            "description": monster.get("description_es", ""),
            "weaknesses": {
                "fuego": int(monster.get("fire", 1)),
                "agua": int(monster.get("water", 1)),
                "rayo": int(monster.get("thunder", 1)),
                "hielo": int(monster.get("ice", 1)),
                "dragon": int(monster.get("dragon", 1)),
                "nitro": int(monster.get("blast", 1)),
                "veneno": int(monster.get("poison", 1)),
                "paralisis": int(monster.get("paralysis", 1)),
                "sueño": int(monster.get("sleep", 1)),
                "stun": int(monster.get("stun", 1))
            },
            "materials": materials,
            "parts": parts
        }
        monster_list.append(monster_data)
        base_id += 1  # Incrementar ID para el siguiente monstruo
    
    return monster_list

# Procesar datos
result = process_monster_data(large_monsters)

class CompactJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, (list, tuple)):
            return '[' + ','.join(
                self.encode(item) if isinstance(item, (dict, list))
                else json.dumps(item, ensure_ascii=False)
                for item in obj
            ) + ']'
        elif isinstance(obj, dict):
            items = []
            for key, value in obj.items():
                colon = ': '
                encoded_value = self.encode(value) if isinstance(value, (dict, list)) else json.dumps(value, ensure_ascii=False)
                items.append(f'"{key}"{colon}{encoded_value}')
            return '{\n  ' + ',\n  '.join(items) + '\n}'
        return json.dumps(obj, ensure_ascii=False)

# Modificar la escritura del archivo para usar el encoder directamente
with open('monsters.json', 'w', encoding='utf-8') as f:
    encoder = CompactJSONEncoder()
    f.write('[\n')
    for i, monster in enumerate(result):
        json_str = encoder.encode(monster)
        f.write(json_str)
        if i < len(result) - 1:
            f.write(',\n')
    f.write('\n]')

print("Archivo JSON generado con éxito: monsters.json")
