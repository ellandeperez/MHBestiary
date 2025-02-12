import json
import os
from urllib.parse import urlparse

def extract_image_paths(monsters):
    """Extrae todas las rutas de imágenes del JSON"""
    paths = set()
    
    for monster in monsters:
        # Imagen principal
        if 'image' in monster:
            paths.add(extract_github_path(monster['image']))
            
        # Imágenes de galería
        if 'gallery' in monster and monster['gallery']:
            for img in monster['gallery']:
                paths.add(extract_github_path(img))
                
        # Imágenes de variantes
        if 'variants' in monster and monster['variants']:
            for variant in monster['variants']:
                if 'image' in variant:
                    paths.add(extract_github_path(variant['image']))
                    
        # Imágenes de materiales
        if 'materials' in monster and monster['materials']:
            for material in monster['materials']:
                if 'icon' in material:
                    paths.add(extract_github_path(material['icon']))

    return paths

def extract_github_path(url):
    """Extrae la ruta local desde una URL de GitHub"""
    parsed = urlparse(url)
    path = parsed.path
    # Eliminar '/blob/main/' y convertir a ruta local
    local_path = path.replace('/ellandeperez/MHBestiary/blob/main/', '')
    # Asegurarse de que empieza con MHImages
    if not local_path.startswith('MHImages'):
        local_path = os.path.join('MHImages', local_path)
    return local_path

def create_folders(base_path, paths):
    """Crea las carpetas necesarias"""
    for path in paths:
        # Crear ruta completa
        full_path = os.path.join(base_path, os.path.dirname(path))
        
        # Crear carpetas si no existen
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path)
                print(f"Creada carpeta: {full_path}")
            except Exception as e:
                print(f"Error creando {full_path}: {str(e)}")

def main():
    # Cargar el JSON
    with open('monsters.json', 'r', encoding='utf-8') as f:
        monsters = json.load(f)
    
    # Extraer rutas
    paths = extract_image_paths(monsters)
    
    # Usar ruta específica para las carpetas
    base_path = r"C:\Users\eperez\Documents\GitHub\MHBestiary"
    create_folders(base_path, paths)
    
    print(f"\nCreadas {len(paths)} carpetas en {base_path}")

if __name__ == "__main__":
    main()