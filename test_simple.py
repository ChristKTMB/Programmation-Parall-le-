#!/usr/bin/env python3
"""
Test simple pour créer QR codes - Version minimale
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

# Test sans dépendances externes d'abord
def test_basic_setup():
    """Test de base sans QR codes"""
    print("🔧 Test de configuration de base...")
    
    # Création dossier
    output_dir = "qr_test_output"
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"✅ Dossier créé: {output_dir}")
    
    # Test données JSON
    test_data = {
        "gov": "cg",
        "id": "gov-cg-20241201-00000001",
        "cert": "occ-2024-000001",
        "prod": "Test_Produit",
        "comp": "TEST_COMPANY",
        "exp": "20251231",
        "ts": datetime.now().strftime('%Y%m%d%H%M%S'),
        "v": "1.0"
    }
    
    # Hash de sécurité
    data_string = json.dumps(test_data, sort_keys=True)
    security_hash = hashlib.sha256(f"{data_string}:CONGO_SECRET".encode()).hexdigest()[:16]
    test_data["hash"] = security_hash
    
    # Sauvegarde test
    test_file = f"{output_dir}/test_data.json"
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"✅ Fichier test créé: {test_file}")
    print(f"📄 Contenu JSON:")
    print(json.dumps(test_data, indent=2))
    
    return output_dir

def check_dependencies():
    """Vérifie les dépendances disponibles"""
    print("\n🔍 Vérification des dépendances...")
    
    deps_status = {}
    
    # Test qrcode
    try:
        import qrcode
        deps_status['qrcode'] = "✅ Disponible"
    except ImportError:
        deps_status['qrcode'] = "❌ Manquant - pip install qrcode[pil]"
    
    # Test Pillow
    try:
        from PIL import Image
        deps_status['Pillow'] = "✅ Disponible"
    except ImportError:
        deps_status['Pillow'] = "❌ Manquant - pip install Pillow"
    
    # Test autres
    try:
        import hashlib, json, datetime
        deps_status['stdlib'] = "✅ Standard libs OK"
    except ImportError:
        deps_status['stdlib'] = "❌ Problème libs standard"
    
    for dep, status in deps_status.items():
        print(f"   {dep}: {status}")
    
    return deps_status

def create_simple_qr_if_possible():
    """Crée un QR simple si possible"""
    print("\n📱 Tentative création QR...")
    
    try:
        import qrcode
        from PIL import Image
        
        # Données QR simples
        qr_data = json.dumps({
            "gov": "cg",
            "id": "test-001",
            "message": "Test QR Congo"
        })
        
        # Création QR
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarde
        output_dir = "qr_test_output"
        img_path = f"{output_dir}/test_qr.png"
        img.save(img_path)
        
        print(f"✅ QR créé: {img_path}")
        print(f"📱 Scannez avec smartphone!")
        print(f"🔍 Données: {qr_data}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Impossible de créer QR: {e}")
        print("💡 Installez: pip install qrcode[pil] Pillow")
        return False
    except Exception as e:
        print(f"❌ Erreur création QR: {e}")
        return False

def create_html_viewer():
    """Crée un visualiseur HTML simple"""
    print("\n🌐 Création visualiseur HTML...")
    
    output_dir = "qr_test_output"
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test QR Congo</title>
    <style>
        body {{ font-family: Arial; margin: 20px; }}
        .header {{ background: #2c5234; color: white; padding: 20px; }}
        .content {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🇨🇩 Test QR Congo</h1>
        <p>Générateur QR codes - République Démocratique du Congo</p>
    </div>
    
    <div class="content">
        <h2>📊 Statut du Test</h2>
        <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p><strong>Dossier:</strong> {output_dir}/</p>
        
        <h3>📱 QR Code Test</h3>
        <p>Si le QR a été généré, il apparaîtra ci-dessous:</p>
        <img src="test_qr.png" alt="QR Test" style="border: 2px solid #2c5234; max-width: 300px;">
        
        <h3>📄 Données Test</h3>
        <p>Fichier JSON: <a href="test_data.json">test_data.json</a></p>
        
        <h3>📞 Prochaines Étapes</h3>
        <ol>
            <li>Vérifier que ce fichier s'affiche correctement</li>
            <li>Scanner le QR code avec smartphone</li>
            <li>Installer dépendances si nécessaire</li>
            <li>Lancer test complet</li>
        </ol>
    </div>
</body>
</html>
"""
    
    html_path = f"{output_dir}/test_viewer.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML créé: {html_path}")
    return html_path

def main():
    print("🇨🇩 TEST SIMPLE QR CONGO")
    print("=" * 30)
    
    # 1. Test de base
    output_dir = test_basic_setup()
    
    # 2. Vérification dépendances
    deps = check_dependencies()
    
    # 3. Tentative QR si possible
    qr_created = create_simple_qr_if_possible()
    
    # 4. Visualiseur HTML
    html_path = create_html_viewer()
    
    # 5. Instructions finales
    print(f"\n🎉 TEST TERMINÉ!")
    print(f"📁 Dossier créé: {output_dir}/")
    print(f"🌐 Ouvrir: {html_path}")
    
    if qr_created:
        print(f"✅ QR code prêt à scanner!")
    else:
        print(f"⚠️  Installer dépendances pour QR:")
        print(f"   pip install qrcode[pil] Pillow")
    
    # Liste des fichiers créés
    print(f"\n📄 Fichiers dans {output_dir}/:")
    try:
        for file in os.listdir(output_dir):
            size = os.path.getsize(f"{output_dir}/{file}")
            print(f"   - {file} ({size} bytes)")
    except:
        print("   (Erreur listage fichiers)")

if __name__ == "__main__":
    main()
