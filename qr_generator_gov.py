#!/usr/bin/env python3
"""
Générateur de codes QR parallélisé pour le gouvernement
Objectif: 100M codes QR/jour avec stockage optimisé
"""

import os
import time
import uuid
import hashlib
import json
from datetime import datetime
from multiprocessing import Pool, Queue, Process, Manager
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import qrcode
from PIL import Image
import psutil
import sqlite3
import redis
from pathlib import Path
import logging

# Configuration
class QRConfig:
    # Performance
    MAX_WORKERS = os.cpu_count() * 2  # Adaptatif selon CPU
    BATCH_SIZE = 1000  # Nombre de QR par lot
    TARGET_QR_PER_DAY = 100_000_000
    TARGET_QR_PER_SECOND = TARGET_QR_PER_DAY // 86400  # ~1157/sec
    
    # Stockage
    OUTPUT_DIR = "qr_codes_gov"
    DB_PATH = "qr_database.db"
    CACHE_TTL = 3600  # 1 heure
    
    # QR Code settings
    QR_VERSION = 1
    QR_ERROR_CORRECT = qrcode.constants.ERROR_CORRECT_L
    QR_BOX_SIZE = 10
    QR_BORDER = 4

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('qr_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QRCodeData:
    """Structure pour données du code QR"""
    def __init__(self, citizen_id: str, document_type: str, expiry_date: str, 
                 security_hash: str = None):
        self.id = str(uuid.uuid4())
        self.citizen_id = citizen_id
        self.document_type = document_type
        self.expiry_date = expiry_date
        self.created_at = datetime.now().isoformat()
        self.security_hash = security_hash or self._generate_security_hash()
        
    def _generate_security_hash(self):
        """Génère un hash de sécurité pour le gouvernement"""
        data = f"{self.citizen_id}:{self.document_type}:{self.expiry_date}:{self.created_at}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_qr_data(self):
        """Convertit en format pour QR Code"""
        return json.dumps({
            'id': self.id,
            'citizen_id': self.citizen_id,
            'type': self.document_type,
            'exp': self.expiry_date,
            'hash': self.security_hash,
            'ts': self.created_at
        }, separators=(',', ':'))  # Format compact

class DatabaseManager:
    """Gestionnaire de base de données optimisé"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données avec index optimisés"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qr_codes (
                id TEXT PRIMARY KEY,
                citizen_id TEXT NOT NULL,
                document_type TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                security_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER
            )
        ''')
        
        # Index pour recherches rapides
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_citizen_id ON qr_codes(citizen_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_document_type ON qr_codes(document_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON qr_codes(created_at)')
        
        conn.commit()
        conn.close()
    
    def save_qr_record(self, qr_data: QRCodeData, file_path: str, file_size: int):
        """Sauvegarde un enregistrement QR en base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO qr_codes 
            (id, citizen_id, document_type, expiry_date, security_hash, created_at, file_path, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            qr_data.id, qr_data.citizen_id, qr_data.document_type,
            qr_data.expiry_date, qr_data.security_hash, qr_data.created_at,
            file_path, file_size
        ))
        
        conn.commit()
        conn.close()

class CacheManager:
    """Gestionnaire de cache Redis (simulation sans Redis installé)"""
    
    def __init__(self):
        self.cache = {}  # Simulation locale du cache
        self.ttl = {}
    
    def get(self, key: str):
        """Récupère une valeur du cache"""
        if key in self.cache:
            if time.time() - self.ttl.get(key, 0) < QRConfig.CACHE_TTL:
                return self.cache[key]
            else:
                del self.cache[key]
                if key in self.ttl:
                    del self.ttl[key]
        return None
    
    def set(self, key: str, value: any):
        """Stocke une valeur dans le cache"""
        self.cache[key] = value
        self.ttl[key] = time.time()

def generate_single_qr(qr_data: QRCodeData, output_dir: str) -> tuple:
    """
    Génère un seul code QR optimisé
    Returns: (success, file_path, file_size, generation_time)
    """
    start_time = time.time()
    
    try:
        # Création du QR Code
        qr = qrcode.QRCode(
            version=QRConfig.QR_VERSION,
            error_correction=QRConfig.QR_ERROR_CORRECT,
            box_size=QRConfig.QR_BOX_SIZE,
            border=QRConfig.QR_BORDER,
        )
        
        qr.add_data(qr_data.to_qr_data())
        qr.make(fit=True)
        
        # Génération de l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarde optimisée
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{qr_data.id}.png")
        img.save(file_path, optimize=True)
        
        file_size = os.path.getsize(file_path)
        generation_time = time.time() - start_time
        
        return True, file_path, file_size, generation_time
        
    except Exception as e:
        logger.error(f"Erreur génération QR {qr_data.id}: {e}")
        return False, None, 0, time.time() - start_time

def process_qr_batch(batch_data: list, output_dir: str, db_path: str) -> dict:
    """
    Traite un lot de codes QR
    Args:
        batch_data: Liste de QRCodeData
        output_dir: Répertoire de sortie
        db_path: Chemin de la base de données
    """
    batch_start = time.time()
    results = {
        'success_count': 0,
        'error_count': 0,
        'total_size': 0,
        'processing_time': 0,
        'batch_id': str(uuid.uuid4())[:8]
    }
    
    db_manager = DatabaseManager(db_path)
    
    for qr_data in batch_data:
        success, file_path, file_size, gen_time = generate_single_qr(qr_data, output_dir)
        
        if success:
            # Sauvegarde en base de données
            db_manager.save_qr_record(qr_data, file_path, file_size)
            results['success_count'] += 1
            results['total_size'] += file_size
        else:
            results['error_count'] += 1
    
    results['processing_time'] = time.time() - batch_start
    return results

class QRGeneratorGov:
    """Générateur de codes QR parallélisé pour le gouvernement"""
    
    def __init__(self):
        self.config = QRConfig()
        self.db_manager = DatabaseManager(self.config.DB_PATH)
        self.cache_manager = CacheManager()
        self.stats = {
            'total_generated': 0,
            'total_errors': 0,
            'total_size': 0,
            'start_time': None,
            'batches_processed': 0
        }
        
        # Création du répertoire de sortie
        Path(self.config.OUTPUT_DIR).mkdir(exist_ok=True)
        
        logger.info(f"QR Generator initialisé - Cible: {self.config.TARGET_QR_PER_DAY:,} QR/jour")
    
    def generate_test_data(self, count: int) -> list:
        """Génère des données de test pour les codes QR"""
        test_data = []
        document_types = ['PASSPORT', 'ID_CARD', 'DRIVER_LICENSE', 'BIRTH_CERT', 'TAX_CERT']
        
        for i in range(count):
            qr_data = QRCodeData(
                citizen_id=f"GOV{i:08d}",
                document_type=document_types[i % len(document_types)],
                expiry_date=f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
            )
            test_data.append(qr_data)
        
        return test_data
    
    def generate_qr_codes_parallel(self, qr_data_list: list, num_workers: int = None) -> dict:
        """
        Génère des codes QR en parallèle
        """
        if num_workers is None:
            num_workers = self.config.MAX_WORKERS
        
        self.stats['start_time'] = time.time()
        total_qr = len(qr_data_list)
        
        logger.info(f"Démarrage génération de {total_qr:,} codes QR avec {num_workers} workers")
        
        # Division en lots
        batches = [qr_data_list[i:i + self.config.BATCH_SIZE] 
                  for i in range(0, len(qr_data_list), self.config.BATCH_SIZE)]
        
        logger.info(f"Traitement de {len(batches)} lots de {self.config.BATCH_SIZE} QR")
        
        # Traitement parallèle
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            for batch in batches:
                future = executor.submit(
                    process_qr_batch, 
                    batch, 
                    self.config.OUTPUT_DIR, 
                    self.config.DB_PATH
                )
                futures.append(future)
            
            # Collecte des résultats
            batch_results = []
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=300)  # 5min timeout par lot
                    batch_results.append(result)
                    self.stats['batches_processed'] += 1
                    
                    # Log de progression
                    if (i + 1) % 10 == 0:
                        progress = ((i + 1) / len(futures)) * 100
                        logger.info(f"Progression: {progress:.1f}% ({i+1}/{len(futures)} lots)")
                        
                except Exception as e:
                    logger.error(f"Erreur lot {i}: {e}")
                    batch_results.append({
                        'success_count': 0, 'error_count': self.config.BATCH_SIZE,
                        'total_size': 0, 'processing_time': 0
                    })
        
        # Calcul des statistiques finales
        self._calculate_final_stats(batch_results)
        
        return self.get_performance_report()
    
    def _calculate_final_stats(self, batch_results: list):
        """Calcule les statistiques finales"""
        for result in batch_results:
            self.stats['total_generated'] += result['success_count']
            self.stats['total_errors'] += result['error_count']
            self.stats['total_size'] += result['total_size']
        
        self.stats['total_time'] = time.time() - self.stats['start_time']
        self.stats['qr_per_second'] = self.stats['total_generated'] / self.stats['total_time']
    
    def get_performance_report(self) -> dict:
        """Génère un rapport de performance détaillé"""
        total_qr = self.stats['total_generated'] + self.stats['total_errors']
        
        report = {
            'summary': {
                'total_qr_requested': total_qr,
                'successful_generated': self.stats['total_generated'],
                'errors': self.stats['total_errors'],
                'success_rate': (self.stats['total_generated'] / total_qr * 100) if total_qr > 0 else 0,
            },
            'performance': {
                'total_time_seconds': round(self.stats['total_time'], 2),
                'qr_per_second': round(self.stats['qr_per_second'], 2),
                'estimated_daily_capacity': int(self.stats['qr_per_second'] * 86400),
                'target_achievement': (self.stats['qr_per_second'] / self.config.TARGET_QR_PER_SECOND * 100)
            },
            'storage': {
                'total_size_mb': round(self.stats['total_size'] / (1024 * 1024), 2),
                'avg_size_per_qr_kb': round(self.stats['total_size'] / self.stats['total_generated'] / 1024, 2) if self.stats['total_generated'] > 0 else 0,
                'estimated_daily_storage_gb': round((self.stats['total_size'] / self.stats['total_generated']) * self.config.TARGET_QR_PER_DAY / (1024**3), 2) if self.stats['total_generated'] > 0 else 0
            },
            'system': {
                'cpu_usage_percent': psutil.cpu_percent(),
                'memory_usage_percent': psutil.virtual_memory().percent,
                'workers_used': self.config.MAX_WORKERS,
                'batches_processed': self.stats['batches_processed']
            }
        }
        
        return report

def benchmark_qr_generation():
    """Benchmark de génération de codes QR"""
    print("🏛️ GÉNÉRATEUR DE CODES QR GOUVERNEMENTAL")
    print("=" * 50)
    
    generator = QRGeneratorGov()
    
    # Test avec différentes tailles
    test_sizes = [1000, 5000, 10000, 25000]  # Tailles de test
    worker_counts = [1, 2, 4, 8, 16]  # Nombre de workers à tester
    
    results = []
    
    for test_size in test_sizes:
        print(f"\n📊 Test avec {test_size:,} codes QR")
        print("-" * 30)
        
        # Génération des données de test
        test_data = generator.generate_test_data(test_size)
        
        for workers in worker_counts:
            if workers <= os.cpu_count() * 2:  # Limite raisonnable
                print(f"⚡ Test avec {workers} workers...")
                
                # Reset stats
                generator.stats = {
                    'total_generated': 0, 'total_errors': 0, 'total_size': 0,
                    'start_time': None, 'batches_processed': 0
                }
                
                # Génération
                report = generator.generate_qr_codes_parallel(test_data, workers)
                results.append({
                    'test_size': test_size,
                    'workers': workers,
                    'report': report
                })
                
                # Affichage des résultats
                perf = report['performance']
                print(f"  ⏱️  Temps: {perf['total_time_seconds']}s")
                print(f"  🚀 QR/sec: {perf['qr_per_second']:.1f}")
                print(f"  🎯 Capacité quotidienne estimée: {perf['estimated_daily_capacity']:,}")
                print(f"  📈 Objectif atteint: {perf['target_achievement']:.1f}%")
    
    return results

if __name__ == "__main__":
    # Lancement du benchmark
    benchmark_results = benchmark_qr_generation()
    
    print("\n" + "=" * 60)
    print("📈 RÉSUMÉ DES PERFORMANCES")
    print("=" * 60)
    
    # Meilleur résultat
    best_result = max(benchmark_results, 
                     key=lambda x: x['report']['performance']['qr_per_second'])
    
    best_perf = best_result['report']['performance']
    print(f"🏆 Meilleure performance:")
    print(f"   - Configuration: {best_result['test_size']:,} QR avec {best_result['workers']} workers")
    print(f"   - Vitesse: {best_perf['qr_per_second']:.1f} QR/seconde")
    print(f"   - Capacité quotidienne: {best_perf['estimated_daily_capacity']:,} QR/jour")
    print(f"   - Objectif 100M/jour: {best_perf['target_achievement']:.1f}% atteint")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS POUR 100M QR/JOUR:")
    target_qr_per_sec = QRConfig.TARGET_QR_PER_DAY // 86400
    current_best = best_perf['qr_per_second']
    
    if current_best >= target_qr_per_sec:
        print(f"✅ Objectif ATTEINT! Configuration actuelle suffisante.")
    else:
        scaling_factor = target_qr_per_sec / current_best
        recommended_workers = int(best_result['workers'] * scaling_factor)
        
        print(f"📊 Facteur d'échelle nécessaire: {scaling_factor:.1f}x")
        print(f"🖥️  Workers recommandés: {recommended_workers}")
        print(f"💻 Serveurs estimés (32 cores): {recommended_workers // 64 + 1}")
        
        # Estimations de stockage
        storage = best_result['report']['storage']
        daily_storage_gb = storage['estimated_daily_storage_gb'] * scaling_factor
        print(f"💾 Stockage quotidien estimé: {daily_storage_gb:.1f} GB/jour")
        print(f"🗄️  Stockage annuel estimé: {daily_storage_gb * 365 / 1024:.1f} TB/an")
