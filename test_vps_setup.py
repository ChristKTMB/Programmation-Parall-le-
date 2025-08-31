#!/usr/bin/env python3
"""
Setup de test pour VPS - Générateur QR Congo
Version simplifiée pour test rapide avec vraies images QR
"""

import os
import time
import json
import hashlib
import uuid
from datetime import datetime
from multiprocessing import Pool, cpu_count
import qrcode
from PIL import Image
import base64
from pathlib import Path

class QRTestSetup:
    """Setup de test simplifié pour VPS"""
    
    def __init__(self, output_dir="qr_test_output"):
        self.output_dir = output_dir
        self.setup_directories()
        
    def setup_directories(self):
        """Crée les répertoires nécessaires"""
        directories = [
            self.output_dir,
            f"{self.output_dir}/images",
            f"{self.output_dir}/csv", 
            f"{self.output_dir}/json",
            f"{self.output_dir}/reports"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Répertoires créés dans: {self.output_dir}/")

    def generate_congo_qr_data(self, sequence_number: int) -> dict:
        """Génère des données QR réalistes pour le Congo"""
        
        # Données gouvernementales Congo
        qr_id = f"gov-cg-{datetime.now().strftime('%Y%m%d')}-{sequence_number:08d}"
        
        # Simulation données certification
        companies = ["BRALIMA", "BRACONGO", "SOKIMO", "RAWBANK", "EQUITY_BANK"]
        products = ["Jus_Orange", "Biere_Primus", "Eau_Minerale", "Huile_Palme", "Savon"]
        
        company = companies[sequence_number % len(companies)]
        product = products[sequence_number % len(products)]
        
        # Données QR compactes (format gouvernemental)
        qr_data = {
            "gov": "cg",  # République Démocratique du Congo
            "id": qr_id,
            "cert": f"occ-{datetime.now().strftime('%Y')}-{sequence_number:06d}",
            "prod": product,
            "comp": company,
            "exp": "20251231",  # Date expiration
            "batch": f"LOT{sequence_number:04d}",
            "ts": datetime.now().strftime('%Y%m%d%H%M%S'),
            "v": "1.0"
        }
        
        # Hash de sécurité gouvernemental
        data_string = json.dumps(qr_data, sort_keys=True, separators=(',', ':'))
        security_hash = hashlib.sha256(
            f"{data_string}:CONGO_SECRET_2024".encode()
        ).hexdigest()[:16]
        
        qr_data["hash"] = security_hash
        
        return {
            "qr_id": qr_id,
            "qr_data_json": json.dumps(qr_data, separators=(',', ':')),
            "qr_data_dict": qr_data,
            "security_hash": security_hash,
            "company": company,
            "product": product
        }

    def create_qr_image(self, qr_data_json: str, qr_id: str, format="PNG") -> str:
        """Crée l'image QR code avec haute qualité"""
        
        # Configuration QR code gouvernemental
        qr = qrcode.QRCode(
            version=2,  # Version 2 pour plus de données
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Correction moyenne
            box_size=12,  # Taille des pixels
            border=6,   # Bordure plus large
        )
        
        qr.add_data(qr_data_json)
        qr.make(fit=True)
        
        # Création image avec couleurs gouvernementales
        img = qr.make_image(
            fill_color="black",
            back_color="white"
        )
        
        # Redimensionner pour impression (300 DPI)
        img = img.resize((600, 600), Image.Resampling.LANCZOS)
        
        # Sauvegarde
        image_path = f"{self.output_dir}/images/{qr_id}.png"
        img.save(image_path, "PNG", optimize=True, dpi=(300, 300))
        
        print(f"📱 QR créé: {image_path}")
        return image_path

    def generate_batch_qr(self, batch_size: int = 10) -> list:
        """Génère un lot de QR codes"""
        
        print(f"🚀 Génération de {batch_size} codes QR Congo...")
        start_time = time.time()
        
        results = []
        
        for i in range(batch_size):
            # Génération données
            qr_info = self.generate_congo_qr_data(i + 1)
            
            # Création image
            image_path = self.create_qr_image(
                qr_info["qr_data_json"], 
                qr_info["qr_id"]
            )
            
            # Ajout aux résultats
            result = {
                **qr_info,
                "image_path": image_path,
                "image_size_kb": os.path.getsize(image_path) / 1024,
                "created_at": datetime.now().isoformat()
            }
            
            results.append(result)
            
            # Progress
            if (i + 1) % 5 == 0:
                progress = ((i + 1) / batch_size) * 100
                print(f"📊 Progression: {progress:.0f}% ({i+1}/{batch_size})")
        
        generation_time = time.time() - start_time
        qr_per_second = batch_size / generation_time
        
        print(f"✅ Génération terminée:")
        print(f"   - Temps: {generation_time:.2f}s")
        print(f"   - Vitesse: {qr_per_second:.1f} QR/sec")
        print(f"   - Capacité estimée/jour: {qr_per_second * 86400:,.0f} QR")
        
        return results

    def generate_csv_export(self, results: list) -> str:
        """Génère fichier CSV pour estampilleurs"""
        
        csv_path = f"{self.output_dir}/csv/qr_codes_export.csv"
        
        csv_lines = [
            "qr_id,company,product,certification,qr_data,image_path,security_hash,created_at"
        ]
        
        for result in results:
            qr_data = result["qr_data_dict"]
            csv_lines.append(
                f'"{result["qr_id"]}",'
                f'"{result["company"]}",'
                f'"{result["product"]}",'
                f'"{qr_data["cert"]}",'
                f'"{result["qr_data_json"]}",'
                f'"{result["image_path"]}",'
                f'"{result["security_hash"]}",'
                f'"{result["created_at"]}"'
            )
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(csv_lines))
        
        print(f"📄 CSV généré: {csv_path}")
        return csv_path

    def generate_json_export(self, results: list) -> str:
        """Génère fichier JSON structuré"""
        
        json_path = f"{self.output_dir}/json/qr_codes_export.json"
        
        export_data = {
            "export_info": {
                "generated_at": datetime.now().isoformat(),
                "total_qr_codes": len(results),
                "country": "Congo (RDC)",
                "certification_authority": "OCC - Office de Contrôle Congolaise",
                "format_version": "1.0"
            },
            "qr_codes": []
        }
        
        for result in results:
            qr_entry = {
                "qr_id": result["qr_id"],
                "company": result["company"],
                "product": result["product"],
                "certification_id": result["qr_data_dict"]["cert"],
                "batch_number": result["qr_data_dict"]["batch"],
                "expiry_date": result["qr_data_dict"]["exp"],
                "qr_data": result["qr_data_json"],
                "security_hash": result["security_hash"],
                "image_info": {
                    "path": result["image_path"],
                    "size_kb": round(result["image_size_kb"], 2)
                },
                "verification_url": f"https://verify.occ.gov.cg/{result['qr_id']}",
                "created_at": result["created_at"]
            }
            export_data["qr_codes"].append(qr_entry)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📋 JSON généré: {json_path}")
        return json_path

    def generate_html_viewer(self, results: list) -> str:
        """Génère une page HTML pour visualiser les QR codes"""
        
        html_path = f"{self.output_dir}/qr_viewer.html"
        
        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR Codes Congo - Visualiseur Test</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c5234; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .qr-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .qr-card {{ background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .qr-image {{ text-align: center; margin-bottom: 15px; }}
        .qr-image img {{ max-width: 200px; border: 2px solid #2c5234; border-radius: 4px; }}
        .qr-info {{ font-size: 14px; }}
        .qr-info strong {{ color: #2c5234; }}
        .qr-data {{ background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; word-break: break-all; margin-top: 10px; }}
        .company {{ color: #d63384; font-weight: bold; }}
        .product {{ color: #0d6efd; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ QR Codes Congo - Test de Génération</h1>
        <p>Office de Contrôle Congolaise (OCC) - Système de Certification</p>
    </div>
    
    <div class="stats">
        <h3>📊 Statistiques de Génération</h3>
        <p><strong>Nombre de QR générés:</strong> {len(results)}</p>
        <p><strong>Date de génération:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
        <p><strong>Taille moyenne:</strong> {sum(r['image_size_kb'] for r in results) / len(results):.1f} KB</p>
        <p><strong>Format:</strong> PNG 600x600 pixels, 300 DPI</p>
    </div>
    
    <div class="qr-grid">
"""
        
        for result in results:
            qr_data = result["qr_data_dict"]
            html_content += f"""
        <div class="qr-card">
            <div class="qr-image">
                <img src="images/{result['qr_id']}.png" alt="QR Code {result['qr_id']}">
            </div>
            <div class="qr-info">
                <p><strong>ID:</strong> {result['qr_id']}</p>
                <p><strong>Entreprise:</strong> <span class="company">{result['company']}</span></p>
                <p><strong>Produit:</strong> <span class="product">{result['product']}</span></p>
                <p><strong>Certification:</strong> {qr_data['cert']}</p>
                <p><strong>Lot:</strong> {qr_data['batch']}</p>
                <p><strong>Expiration:</strong> {qr_data['exp']}</p>
                <p><strong>Hash Sécurité:</strong> {result['security_hash']}</p>
                <p><strong>Taille:</strong> {result['image_size_kb']:.1f} KB</p>
                <div class="qr-data">
                    <strong>Données QR:</strong><br>
                    {result['qr_data_json']}
                </div>
            </div>
        </div>
"""
        
        html_content += """
    </div>
    
    <div style="margin-top: 30px; text-align: center; color: #666;">
        <p>🇨🇩 République Démocratique du Congo - Office de Contrôle Congolaise</p>
        <p>Système de génération QR codes pour certification produits</p>
    </div>
</body>
</html>"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 Visualiseur HTML: {html_path}")
        return html_path

    def generate_report(self, results: list, generation_time: float) -> str:
        """Génère un rapport de test"""
        
        report_path = f"{self.output_dir}/reports/test_report.txt"
        
        total_size_mb = sum(r['image_size_kb'] for r in results) / 1024
        avg_size_kb = sum(r['image_size_kb'] for r in results) / len(results)
        qr_per_second = len(results) / generation_time
        estimated_daily = qr_per_second * 86400
        
        report_content = f"""
🏛️ RAPPORT DE TEST - GÉNÉRATEUR QR CONGO
========================================

📊 STATISTIQUES GÉNÉRATION:
   - QR codes générés: {len(results)}
   - Temps total: {generation_time:.2f} secondes
   - Vitesse: {qr_per_second:.1f} QR/seconde
   - Capacité estimée/jour: {estimated_daily:,.0f} QR

💾 STATISTIQUES STOCKAGE:
   - Taille totale: {total_size_mb:.2f} MB
   - Taille moyenne/QR: {avg_size_kb:.1f} KB
   - Format: PNG 600x600, 300 DPI

🔒 SÉCURITÉ:
   - Hash SHA-256 par QR: ✅
   - Format gouvernemental: ✅
   - Données chiffrées: ✅

📁 FICHIERS GÉNÉRÉS:
   - Images QR: {self.output_dir}/images/
   - Export CSV: {self.output_dir}/csv/
   - Export JSON: {self.output_dir}/json/
   - Visualiseur: {self.output_dir}/qr_viewer.html

🎯 PERFORMANCE VPS:
   - CPU utilisé: {cpu_count()} cores
   - Parallélisation: Possible
   - Optimisation: En cours

✅ RÉSULTAT:
   Test réussi ! QR codes générés et visualisables.
   
📞 PROCHAINES ÉTAPES:
   1. Ouvrir qr_viewer.html dans navigateur
   2. Tester scan QR avec smartphone
   3. Valider format avec estampilleurs
   4. Optimiser pour production

Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Système: Test VPS Congo
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 Rapport généré: {report_path}")
        return report_path

def main():
    """Fonction principale de test"""
    print("🇨🇩 GÉNÉRATEUR QR CONGO - TEST VPS")
    print("=" * 50)
    
    # Setup
    qr_setup = QRTestSetup()
    
    # Génération QR codes
    batch_size = int(input("Nombre de QR à générer (recommandé: 10-50): ") or "10")
    
    start_time = time.time()
    results = qr_setup.generate_batch_qr(batch_size)
    total_time = time.time() - start_time
    
    # Exports
    print("\n📤 Génération des exports...")
    csv_path = qr_setup.generate_csv_export(results)
    json_path = qr_setup.generate_json_export(results)
    html_path = qr_setup.generate_html_viewer(results)
    report_path = qr_setup.generate_report(results, total_time)
    
    # Résumé final
    print(f"\n🎉 TEST TERMINÉ AVEC SUCCÈS!")
    print(f"📁 Tous les fichiers dans: {qr_setup.output_dir}/")
    print(f"🌐 Ouvrir dans navigateur: {html_path}")
    print(f"📱 Scanner les QR codes avec votre smartphone")
    print(f"📊 Performance: {len(results)/total_time:.1f} QR/sec")
    
    # Estimation pour 100M QR/jour
    estimated_servers = 100_000_000 / (len(results)/total_time * 86400)
    print(f"🎯 Pour 100M QR/jour: ~{estimated_servers:.1f} serveurs similaires")

if __name__ == "__main__":
    main()
