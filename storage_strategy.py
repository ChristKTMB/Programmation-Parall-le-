#!/usr/bin/env python3
"""
Stratégie de stockage avancée pour 100M codes QR/jour
Architecture de stockage distribuée et optimisée
"""

import os
import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sqlite3
import threading
from dataclasses import dataclass
from enum import Enum

class StorageType(Enum):
    """Types de stockage disponibles"""
    LOCAL_SSD = "local_ssd"
    NETWORK_SAN = "network_san" 
    CLOUD_S3 = "cloud_s3"
    DISTRIBUTED_FS = "distributed_fs"

class CompressionLevel(Enum):
    """Niveaux de compression"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

@dataclass
class StorageConfig:
    """Configuration de stockage"""
    # Répartition par type de stockage
    hot_storage_days: int = 7      # Stockage rapide (SSD)
    warm_storage_days: int = 90    # Stockage intermédiaire
    cold_storage_days: int = 2555  # Stockage long terme (7 ans)
    
    # Répartition géographique  
    primary_datacenter: str = "dc1"
    backup_datacenters: List[str] = None
    
    # Compression et optimisation
    compression_level: CompressionLevel = CompressionLevel.MEDIUM
    enable_deduplication: bool = True
    
    # Sharding
    shards_per_day: int = 24  # 1 shard par heure
    shard_size_limit_gb: int = 50
    
    def __post_init__(self):
        if self.backup_datacenters is None:
            self.backup_datacenters = ["dc2", "dc3"]

class QRStorageManager:
    """Gestionnaire de stockage avancé pour codes QR"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.storage_stats = {
            'total_files': 0,
            'total_size_bytes': 0,
            'files_by_storage_type': {},
            'daily_stats': {}
        }
        self._init_storage_structure()
        self._init_database()
    
    def _init_storage_structure(self):
        """Initialise la structure de stockage hiérarchique"""
        base_paths = {
            'hot': 'storage/hot',      # SSD rapide
            'warm': 'storage/warm',    # SAN/NAS
            'cold': 'storage/cold',    # Cloud/Tape
            'temp': 'storage/temp'     # Temporaire
        }
        
        for storage_type, path in base_paths.items():
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialise la base de données de métadonnées"""
        self.db_path = "qr_storage_metadata.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table principale des métadonnées
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qr_metadata (
                qr_id TEXT PRIMARY KEY,
                citizen_id TEXT NOT NULL,
                document_type TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                storage_type TEXT NOT NULL,
                shard_id TEXT NOT NULL,
                compression_ratio REAL,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                checksum TEXT NOT NULL,
                backup_locations TEXT  -- JSON array
            )
        ''')
        
        # Table de sharding
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS storage_shards (
                shard_id TEXT PRIMARY KEY,
                created_at TIMESTAMP NOT NULL,
                storage_type TEXT NOT NULL,
                current_size_bytes INTEGER DEFAULT 0,
                file_count INTEGER DEFAULT 0,
                is_sealed BOOLEAN DEFAULT FALSE,
                backup_status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Index pour optimiser les requêtes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON qr_metadata(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_storage_type ON qr_metadata(storage_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_citizen_id ON qr_metadata(citizen_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_shard_id ON qr_metadata(shard_id)')
        
        conn.commit()
        conn.close()
    
    def _determine_storage_tier(self, created_at: datetime) -> str:
        """Détermine le niveau de stockage selon l'âge"""
        age_days = (datetime.now() - created_at).days
        
        if age_days <= self.config.hot_storage_days:
            return 'hot'
        elif age_days <= self.config.warm_storage_days:
            return 'warm'
        else:
            return 'cold'
    
    def _generate_shard_id(self, created_at: datetime, storage_type: str) -> str:
        """Génère un ID de shard basé sur la date et le type"""
        date_str = created_at.strftime("%Y%m%d")
        hour = created_at.hour
        shard_hour = (hour // (24 // self.config.shards_per_day))
        return f"{storage_type}_{date_str}_{shard_hour:02d}"
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calcule le checksum MD5 d'un fichier"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def store_qr_file(self, qr_id: str, citizen_id: str, document_type: str,
                     source_file_path: str, created_at: datetime = None) -> Dict:
        """
        Stocke un fichier QR avec stratégie de stockage intelligente
        
        Returns:
            Dict avec informations de stockage
        """
        if created_at is None:
            created_at = datetime.now()
        
        # Détermination du niveau de stockage
        storage_tier = self._determine_storage_tier(created_at)
        shard_id = self._generate_shard_id(created_at, storage_tier)
        
        # Construction du chemin de destination
        year_month = created_at.strftime("%Y/%m")
        day = created_at.strftime("%d")
        dest_dir = f"storage/{storage_tier}/{year_month}/{day}/{shard_id}"
        Path(dest_dir).mkdir(parents=True, exist_ok=True)
        
        dest_file_path = f"{dest_dir}/{qr_id}.png"
        
        # Copie et compression si nécessaire
        file_size = self._copy_and_optimize_file(source_file_path, dest_file_path)
        
        # Calcul du checksum
        checksum = self._calculate_checksum(dest_file_path)
        
        # Sauvegarde des métadonnées
        storage_info = {
            'qr_id': qr_id,
            'citizen_id': citizen_id,
            'document_type': document_type,
            'created_at': created_at,
            'file_path': dest_file_path,
            'file_size': file_size,
            'storage_type': storage_tier,
            'shard_id': shard_id,
            'checksum': checksum,
            'backup_locations': []
        }
        
        self._save_metadata(storage_info)
        self._update_shard_stats(shard_id, storage_tier, file_size)
        
        # Planification des sauvegardes
        if storage_tier in ['hot', 'warm']:
            self._schedule_backup(storage_info)
        
        return storage_info
    
    def _copy_and_optimize_file(self, source: str, dest: str) -> int:
        """Copie et optimise un fichier selon le niveau de compression"""
        import shutil
        from PIL import Image
        
        if self.config.compression_level == CompressionLevel.NONE:
            shutil.copy2(source, dest)
        else:
            # Récompression selon le niveau
            img = Image.open(source)
            
            quality_map = {
                CompressionLevel.LOW: 95,
                CompressionLevel.MEDIUM: 85,
                CompressionLevel.HIGH: 75
            }
            
            quality = quality_map.get(self.config.compression_level, 85)
            img.save(dest, "PNG", optimize=True, compress_level=quality//10)
        
        return os.path.getsize(dest)
    
    def _save_metadata(self, storage_info: Dict):
        """Sauvegarde les métadonnées en base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO qr_metadata 
            (qr_id, citizen_id, document_type, created_at, file_path, file_size,
             storage_type, shard_id, checksum, backup_locations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            storage_info['qr_id'],
            storage_info['citizen_id'], 
            storage_info['document_type'],
            storage_info['created_at'].isoformat(),
            storage_info['file_path'],
            storage_info['file_size'],
            storage_info['storage_type'],
            storage_info['shard_id'],
            storage_info['checksum'],
            json.dumps(storage_info['backup_locations'])
        ))
        
        conn.commit()
        conn.close()
    
    def _update_shard_stats(self, shard_id: str, storage_type: str, file_size: int):
        """Met à jour les statistiques du shard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Mise à jour ou création du shard
        cursor.execute('''
            INSERT OR IGNORE INTO storage_shards 
            (shard_id, created_at, storage_type) 
            VALUES (?, ?, ?)
        ''', (shard_id, datetime.now().isoformat(), storage_type))
        
        cursor.execute('''
            UPDATE storage_shards 
            SET current_size_bytes = current_size_bytes + ?,
                file_count = file_count + 1
            WHERE shard_id = ?
        ''', (file_size, shard_id))
        
        # Vérification si le shard doit être scellé
        cursor.execute('''
            SELECT current_size_bytes FROM storage_shards WHERE shard_id = ?
        ''', (shard_id,))
        
        current_size = cursor.fetchone()[0]
        if current_size > self.config.shard_size_limit_gb * 1024 * 1024 * 1024:
            cursor.execute('''
                UPDATE storage_shards SET is_sealed = TRUE WHERE shard_id = ?
            ''', (shard_id,))
        
        conn.commit()
        conn.close()
    
    def _schedule_backup(self, storage_info: Dict):
        """Planifie la sauvegarde vers les datacenters secondaires"""
        # Simulation de planification de backup
        backup_locations = []
        for dc in self.config.backup_datacenters:
            backup_path = f"{dc}:{storage_info['file_path']}"
            backup_locations.append(backup_path)
        
        storage_info['backup_locations'] = backup_locations
        # Ici, on planifierait les tâches de backup asynchrones
    
    def retrieve_qr_file(self, qr_id: str) -> Optional[Dict]:
        """Récupère les informations d'un fichier QR"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM qr_metadata WHERE qr_id = ?
        ''', (qr_id,))
        
        row = cursor.fetchone()
        if row:
            # Mise à jour des stats d'accès
            cursor.execute('''
                UPDATE qr_metadata 
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE qr_id = ?
            ''', (datetime.now().isoformat(), qr_id))
            
            conn.commit()
        
        conn.close()
        return row
    
    def migrate_old_files(self):
        """Migre les anciens fichiers vers les niveaux de stockage appropriés"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recherche des fichiers à migrer
        cursor.execute('''
            SELECT qr_id, created_at, storage_type, file_path
            FROM qr_metadata 
            WHERE storage_type != ?
        ''', ('cold',))
        
        files_to_migrate = cursor.fetchall()
        
        for qr_id, created_at_str, current_storage, file_path in files_to_migrate:
            created_at = datetime.fromisoformat(created_at_str)
            new_storage_tier = self._determine_storage_tier(created_at)
            
            if new_storage_tier != current_storage:
                # Migration nécessaire
                self._migrate_file(qr_id, file_path, current_storage, new_storage_tier)
        
        conn.close()
    
    def _migrate_file(self, qr_id: str, old_path: str, old_tier: str, new_tier: str):
        """Migre un fichier vers un nouveau niveau de stockage"""
        # Construction du nouveau chemin
        # Implémentation de la migration...
        pass
    
    def get_storage_statistics(self) -> Dict:
        """Retourne les statistiques de stockage détaillées"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Stats globales
        cursor.execute('''
            SELECT 
                COUNT(*) as total_files,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size
            FROM qr_metadata
        ''')
        global_stats = cursor.fetchone()
        
        # Stats par type de stockage
        cursor.execute('''
            SELECT 
                storage_type,
                COUNT(*) as file_count,
                SUM(file_size) as total_size
            FROM qr_metadata
            GROUP BY storage_type
        ''')
        storage_type_stats = cursor.fetchall()
        
        # Stats par shard
        cursor.execute('''
            SELECT 
                shard_id,
                storage_type,
                file_count,
                current_size_bytes,
                is_sealed
            FROM storage_shards
            ORDER BY created_at DESC
            LIMIT 20
        ''')
        recent_shards = cursor.fetchall()
        
        conn.close()
        
        return {
            'global': {
                'total_files': global_stats[0],
                'total_size_gb': round(global_stats[1] / (1024**3), 2),
                'avg_file_size_kb': round(global_stats[2] / 1024, 2)
            },
            'by_storage_type': {
                row[0]: {
                    'file_count': row[1],
                    'total_size_gb': round(row[2] / (1024**3), 2)
                } for row in storage_type_stats
            },
            'recent_shards': [
                {
                    'shard_id': row[0],
                    'storage_type': row[1],
                    'file_count': row[2],
                    'size_gb': round(row[3] / (1024**3), 2),
                    'is_sealed': bool(row[4])
                } for row in recent_shards
            ]
        }
    
    def estimate_daily_storage_needs(self, qr_per_day: int, avg_file_size_kb: float) -> Dict:
        """Estime les besoins de stockage quotidiens"""
        daily_size_gb = (qr_per_day * avg_file_size_kb) / (1024 * 1024)
        
        # Répartition par niveau de stockage
        hot_size = daily_size_gb * (self.config.hot_storage_days / 365)
        warm_size = daily_size_gb * (self.config.warm_storage_days / 365)
        cold_size = daily_size_gb * (self.config.cold_storage_days / 365)
        
        return {
            'daily_generation_gb': round(daily_size_gb, 2),
            'storage_needs': {
                'hot_storage_gb': round(hot_size * self.config.hot_storage_days, 2),
                'warm_storage_gb': round(warm_size * self.config.warm_storage_days, 2),
                'cold_storage_tb': round(cold_size * self.config.cold_storage_days / 1024, 2)
            },
            'annual_growth_tb': round(daily_size_gb * 365 / 1024, 2),
            'backup_multiplier': len(self.config.backup_datacenters) + 1
        }

# Exemple d'utilisation et test
if __name__ == "__main__":
    print("🗄️ STRATÉGIE DE STOCKAGE GOUVERNEMENTALE")
    print("=" * 50)
    
    # Configuration
    config = StorageConfig(
        hot_storage_days=7,
        warm_storage_days=90, 
        cold_storage_days=2555,  # 7 ans
        shards_per_day=24,
        compression_level=CompressionLevel.MEDIUM
    )
    
    # Initialisation du gestionnaire
    storage_manager = QRStorageManager(config)
    
    # Simulation de stockage
    print("📊 Simulation de stockage...")
    
    # Estimation pour 100M QR/jour
    daily_needs = storage_manager.estimate_daily_storage_needs(
        qr_per_day=100_000_000,
        avg_file_size_kb=5.0  # 5KB par QR en moyenne
    )
    
    print(f"\n💾 BESOINS DE STOCKAGE ESTIMÉS:")
    print(f"   - Génération quotidienne: {daily_needs['daily_generation_gb']:,} GB/jour")
    print(f"   - Stockage HOT (7 jours): {daily_needs['storage_needs']['hot_storage_gb']:,} GB")
    print(f"   - Stockage WARM (90 jours): {daily_needs['storage_needs']['warm_storage_gb']:,} GB") 
    print(f"   - Stockage COLD (7 ans): {daily_needs['storage_needs']['cold_storage_tb']:,} TB")
    print(f"   - Croissance annuelle: {daily_needs['annual_growth_tb']:,} TB/an")
    print(f"   - Facteur de sauvegarde: {daily_needs['backup_multiplier']}x")
    
    total_storage_tb = (
        daily_needs['storage_needs']['hot_storage_gb'] / 1024 +
        daily_needs['storage_needs']['warm_storage_gb'] / 1024 +
        daily_needs['storage_needs']['cold_storage_tb']
    ) * daily_needs['backup_multiplier']
    
    print(f"\n🎯 STOCKAGE TOTAL REQUIS: {total_storage_tb:,.1f} TB")
    
    # Recommandations d'infrastructure
    print(f"\n🏗️ RECOMMANDATIONS INFRASTRUCTURE:")
    print(f"   - SSD haute performance: {daily_needs['storage_needs']['hot_storage_gb'] * daily_needs['backup_multiplier'] / 1024:.1f} TB")
    print(f"   - SAN/NAS Enterprise: {daily_needs['storage_needs']['warm_storage_gb'] * daily_needs['backup_multiplier'] / 1024:.1f} TB")
    print(f"   - Cloud/Tape Storage: {daily_needs['storage_needs']['cold_storage_tb'] * daily_needs['backup_multiplier']:.1f} TB")
    
    # Coûts estimés (ordres de grandeur)
    ssd_cost_per_tb = 200  # EUR/TB/an
    san_cost_per_tb = 100  # EUR/TB/an  
    cloud_cost_per_tb = 25  # EUR/TB/an
    
    hot_cost = (daily_needs['storage_needs']['hot_storage_gb'] / 1024) * ssd_cost_per_tb * daily_needs['backup_multiplier']
    warm_cost = (daily_needs['storage_needs']['warm_storage_gb'] / 1024) * san_cost_per_tb * daily_needs['backup_multiplier']
    cold_cost = daily_needs['storage_needs']['cold_storage_tb'] * cloud_cost_per_tb * daily_needs['backup_multiplier']
    
    total_annual_cost = hot_cost + warm_cost + cold_cost
    
    print(f"\n💰 COÛTS ESTIMÉS (par an):")
    print(f"   - Stockage HOT: {hot_cost:,.0f} €/an")
    print(f"   - Stockage WARM: {warm_cost:,.0f} €/an")
    print(f"   - Stockage COLD: {cold_cost:,.0f} €/an")
    print(f"   - TOTAL: {total_annual_cost:,.0f} €/an")
