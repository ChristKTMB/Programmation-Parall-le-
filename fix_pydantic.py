#!/usr/bin/env python3
"""
Script pour corriger l'erreur Pydantic regex -> pattern
"""

import os
import re

def fix_pydantic_regex(file_path):
    """Remplace regex= par pattern= dans les fichiers Python"""
    if not os.path.exists(file_path):
        print(f"❌ Fichier non trouvé: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer regex= par pattern=
    new_content = re.sub(r'regex=', 'pattern=', content)
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Corrigé: {file_path}")
        return True
    else:
        print(f"ℹ️  Aucune correction nécessaire: {file_path}")
        return False

def main():
    print("🔧 Correction erreur Pydantic regex -> pattern")
    print("=" * 50)
    
    # Fichiers à corriger
    files_to_fix = [
        'main_api.py',
        'app/main_api.py',
        'src/main_api.py',
        'api/main_api.py'
    ]
    
    corrections_made = 0
    
    for file_path in files_to_fix:
        if fix_pydantic_regex(file_path):
            corrections_made += 1
    
    if corrections_made > 0:
        print(f"\n✅ {corrections_made} fichier(s) corrigé(s)")
        print("🔄 Redémarrez les containers: docker-compose restart")
    else:
        print("\nℹ️  Aucune correction nécessaire")

if __name__ == "__main__":
    main()
