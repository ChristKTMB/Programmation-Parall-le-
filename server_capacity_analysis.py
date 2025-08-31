#!/usr/bin/env python3
"""
Analyse de capacité pour serveur spécifique
Spécifications: 18 vCPU, 96GB RAM, 350GB NVMe
Calcul précis de la génération QR possible
"""

import time
from datetime import datetime, timedelta

class ServerSpecs:
    """Spécifications du serveur"""
    vcpu_cores = 18
    ram_gb = 96
    storage_nvme_gb = 350  # ou 700GB SSD
    storage_ssd_gb = 700
    traffic_tb_monthly = 32
    snapshots = 3

class QRPerformanceCalculator:
    """Calculateur de performance QR pour serveur spécifique"""
    
    def __init__(self, server_specs: ServerSpecs):
        self.server = server_specs
        self.qr_size_kb = 5  # Taille moyenne d'un QR en KB
        self.metadata_overhead = 0.2  # 20% overhead pour métadonnées
        
    def calculate_cpu_capacity(self):
        """Calcule la capacité basée sur le CPU"""
        # Basé sur nos tests : ~1000-2000 QR/sec par core en conditions optimales
        # Soyons conservateurs : 800 QR/sec par vCPU core
        qr_per_second_per_core = 800  # Conservative estimate
        
        total_qr_per_second = self.server.vcpu_cores * qr_per_second_per_core
        total_qr_per_day = total_qr_per_second * 86400  # 24h * 3600s
        
        return {
            'qr_per_second': total_qr_per_second,
            'qr_per_day': total_qr_per_day,
            'limiting_factor': 'CPU'
        }
    
    def calculate_ram_capacity(self):
        """Calcule la capacité basée sur la RAM"""
        # Estimation: 100MB pour l'OS/système + processus QR
        system_ram_gb = 2
        available_ram_gb = self.server.ram_gb - system_ram_gb
        
        # Chaque worker process utilise ~500MB en moyenne
        worker_ram_mb = 500
        max_workers = int((available_ram_gb * 1024) / worker_ram_mb)
        
        # Cache RAM pour QR récents (améliore les performances)
        cache_ram_gb = min(20, available_ram_gb * 0.3)
        qr_cache_count = int((cache_ram_gb * 1024 * 1024) / self.qr_size_kb)
        
        return {
            'max_concurrent_workers': max_workers,
            'available_ram_gb': available_ram_gb,
            'qr_cache_capacity': qr_cache_count,
            'limiting_factor': 'RAM'
        }
    
    def calculate_storage_capacity(self):
        """Calcule la capacité de stockage"""
        # Option 1: NVMe 350GB
        nvme_capacity = self._calculate_storage_for_disk(self.server.storage_nvme_gb)
        
        # Option 2: SSD 700GB  
        ssd_capacity = self._calculate_storage_for_disk(self.server.storage_ssd_gb)
        
        return {
            'nvme_350gb': nvme_capacity,
            'ssd_700gb': ssd_capacity
        }
    
    def _calculate_storage_for_disk(self, disk_gb):
        """Calcule la capacité pour un disque donné"""
        # Réservation système (OS, logs, tmp)
        system_reserved_gb = 50
        available_gb = disk_gb - system_reserved_gb
        
        # Taille effective avec overhead
        qr_size_with_overhead_kb = self.qr_size_kb * (1 + self.metadata_overhead)
        
        # Nombre de QR stockables
        total_qr_capacity = int((available_gb * 1024 * 1024) / qr_size_with_overhead_kb)
        
        # Capacité quotidienne selon stratégie de rétention
        retention_strategies = {
            'hot_only_7_days': total_qr_capacity / 7,  # Tout en hot storage
            'hot_warm_30_days': total_qr_capacity / 30,  # Mix hot/warm
            'archive_daily': total_qr_capacity  # Archive quotidienne vers cloud
        }
        
        return {
            'total_qr_capacity': total_qr_capacity,
            'available_gb': available_gb,
            'daily_capacity_strategies': retention_strategies
        }
    
    def calculate_network_capacity(self):
        """Calcule la capacité réseau"""
        # Traffic mensuel: 32TB
        daily_traffic_gb = (self.server.traffic_tb_monthly * 1024) / 30
        
        # Taille moyenne d'une requête QR (requête + réponse)
        request_size_kb = 2  # Requête JSON
        response_size_kb = self.qr_size_kb + 1  # QR + métadonnées
        total_transfer_per_qr_kb = request_size_kb + response_size_kb
        
        # Nombre de QR possibles avec la bande passante
        qr_per_day_network = int((daily_traffic_gb * 1024 * 1024) / total_transfer_per_qr_kb)
        
        return {
            'daily_traffic_gb': daily_traffic_gb,
            'qr_per_day_network_limit': qr_per_day_network,
            'transfer_per_qr_kb': total_transfer_per_qr_kb
        }
    
    def get_comprehensive_analysis(self):
        """Analyse complète de la capacité"""
        cpu_analysis = self.calculate_cpu_capacity()
        ram_analysis = self.calculate_ram_capacity()
        storage_analysis = self.calculate_storage_capacity()
        network_analysis = self.calculate_network_capacity()
        
        # Détermination du facteur limitant
        capacities = {
            'CPU': cpu_analysis['qr_per_day'],
            'Network': network_analysis['qr_per_day_network_limit'],
            'Storage_NVMe_hot': storage_analysis['nvme_350gb']['daily_capacity_strategies']['hot_only_7_days'],
            'Storage_NVMe_archive': storage_analysis['nvme_350gb']['daily_capacity_strategies']['archive_daily'],
            'Storage_SSD_hot': storage_analysis['ssd_700gb']['daily_capacity_strategies']['hot_only_7_days'], 
            'Storage_SSD_archive': storage_analysis['ssd_700gb']['daily_capacity_strategies']['archive_daily']
        }
        
        limiting_factor = min(capacities.keys(), key=lambda k: capacities[k])
        max_realistic_capacity = capacities[limiting_factor]
        
        return {
            'server_specs': {
                'vcpu_cores': self.server.vcpu_cores,
                'ram_gb': self.server.ram_gb,
                'storage_options': f"{self.server.storage_nvme_gb}GB NVMe ou {self.server.storage_ssd_gb}GB SSD",
                'monthly_traffic_tb': self.server.traffic_tb_monthly
            },
            'capacity_analysis': {
                'cpu_limited': cpu_analysis['qr_per_day'],
                'network_limited': network_analysis['qr_per_day_network_limit'],
                'storage_nvme_limited': storage_analysis['nvme_350gb']['daily_capacity_strategies']['archive_daily'],
                'storage_ssd_limited': storage_analysis['ssd_700gb']['daily_capacity_strategies']['archive_daily']
            },
            'bottleneck': {
                'limiting_factor': limiting_factor,
                'max_daily_capacity': int(max_realistic_capacity),
                'capacity_vs_target': (max_realistic_capacity / 100_000_000) * 100  # vs 100M target
            },
            'recommendations': self._generate_recommendations(capacities),
            'performance_details': {
                'cpu': cpu_analysis,
                'ram': ram_analysis,
                'storage': storage_analysis,
                'network': network_analysis
            }
        }
    
    def _generate_recommendations(self, capacities):
        """Génère des recommandations d'optimisation"""
        recommendations = []
        
        # Analyse CPU
        if capacities['CPU'] > 100_000_000:
            recommendations.append("✅ CPU suffisant pour l'objectif 100M QR/jour")
        else:
            recommendations.append("⚠️ CPU insuffisant - considérer plus de cores ou optimisation")
        
        # Analyse stockage
        if capacities['Storage_SSD_archive'] > capacities['Storage_NVMe_archive']:
            recommendations.append("💾 SSD 700GB recommandé vs NVMe 350GB pour plus de capacité")
        
        if min(capacities['Storage_NVMe_hot'], capacities['Storage_SSD_hot']) < 100_000_000:
            recommendations.append("🔄 Implémentation d'archivage automatique vers cloud recommandée")
        
        # Analyse réseau
        if capacities['Network'] < 100_000_000:
            recommendations.append("🌐 Optimisation réseau nécessaire (compression, CDN)")
        
        return recommendations

def run_server_analysis():
    """Lance l'analyse complète du serveur"""
    print("🖥️ ANALYSE DE CAPACITÉ - SERVEUR SPÉCIFIQUE")
    print("=" * 60)
    
    server = ServerSpecs()
    calculator = QRPerformanceCalculator(server)
    
    print(f"📋 SPÉCIFICATIONS SERVEUR:")
    print(f"   - CPU: {server.vcpu_cores} vCPU cores")
    print(f"   - RAM: {server.ram_gb} GB")
    print(f"   - Stockage: {server.storage_nvme_gb} GB NVMe OU {server.storage_ssd_gb} GB SSD")
    print(f"   - Traffic: {server.traffic_tb_monthly} TB/mois")
    print(f"   - Snapshots: {server.snapshots}")
    
    # Analyse complète
    analysis = calculator.get_comprehensive_analysis()
    
    print(f"\n🎯 CAPACITÉ MAXIMALE QUOTIDIENNE:")
    print(f"   - CPU: {analysis['capacity_analysis']['cpu_limited']:,.0f} QR/jour")
    print(f"   - Réseau: {analysis['capacity_analysis']['network_limited']:,.0f} QR/jour")
    print(f"   - NVMe 350GB: {analysis['capacity_analysis']['storage_nvme_limited']:,.0f} QR/jour")
    print(f"   - SSD 700GB: {analysis['capacity_analysis']['storage_ssd_limited']:,.0f} QR/jour")
    
    print(f"\n🚨 FACTEUR LIMITANT:")
    bottleneck = analysis['bottleneck']
    print(f"   - Limitation: {bottleneck['limiting_factor']}")
    print(f"   - Capacité max réaliste: {bottleneck['max_daily_capacity']:,.0f} QR/jour")
    print(f"   - Objectif 100M atteint: {bottleneck['capacity_vs_target']:.1f}%")
    
    if bottleneck['max_daily_capacity'] >= 100_000_000:
        print(f"   ✅ OBJECTIF ATTEIGNABLE avec ce serveur!")
    else:
        ratio_needed = 100_000_000 / bottleneck['max_daily_capacity']
        print(f"   ⚠️ Il faudrait {ratio_needed:.1f}x serveurs similaires")
    
    print(f"\n💡 RECOMMANDATIONS:")
    for rec in analysis['recommendations']:
        print(f"   {rec}")
    
    # Scénarios d'optimisation
    print(f"\n🔧 SCÉNARIOS D'OPTIMISATION:")
    
    # Scénario 1: Stockage NVMe avec archivage cloud
    print(f"   📦 Scénario NVMe + Cloud:")
    print(f"      - Stockage local: 7 jours en NVMe")
    print(f"      - Archive cloud: automatique")
    print(f"      - Capacité: {analysis['capacity_analysis']['storage_nvme_limited']:,.0f} QR/jour")
    
    # Scénario 2: Stockage SSD avec archivage cloud  
    print(f"   📦 Scénario SSD + Cloud:")
    print(f"      - Stockage local: 14 jours en SSD")
    print(f"      - Archive cloud: automatique") 
    print(f"      - Capacité: {analysis['capacity_analysis']['storage_ssd_limited']:,.0f} QR/jour")
    
    # Détails par composant
    perf = analysis['performance_details']
    
    print(f"\n📊 DÉTAILS PERFORMANCE:")
    print(f"   🖥️ CPU:")
    print(f"      - {perf['cpu']['qr_per_second']:,.0f} QR/seconde")
    print(f"      - {perf['cpu']['qr_per_day']:,.0f} QR/jour")
    
    print(f"   🧠 RAM:")
    print(f"      - {perf['ram']['max_concurrent_workers']} workers max")
    print(f"      - {perf['ram']['available_ram_gb']:.1f} GB disponible")
    print(f"      - {perf['ram']['qr_cache_capacity']:,.0f} QR en cache")
    
    print(f"   🌐 Réseau:")
    print(f"      - {perf['network']['daily_traffic_gb']:.1f} GB/jour disponible")
    print(f"      - {perf['network']['qr_per_day_network_limit']:,.0f} QR/jour max")
    
    return analysis

if __name__ == "__main__":
    analysis_result = run_server_analysis()
    
    # Résumé final
    max_capacity = analysis_result['bottleneck']['max_daily_capacity']
    target = 100_000_000
    
    print(f"\n" + "=" * 60)
    print(f"🏆 VERDICT FINAL")
    print(f"=" * 60)
    
    if max_capacity >= target:
        surplus = ((max_capacity / target) - 1) * 100
        print(f"✅ CE SERVEUR PEUT GÉNÉRER {max_capacity:,.0f} QR/JOUR")
        print(f"🎯 OBJECTIF 100M: LARGEMENT DÉPASSÉ (+{surplus:.1f}%)")
        print(f"💪 Marge de sécurité: {max_capacity - target:,.0f} QR/jour")
    else:
        deficit = ((target / max_capacity) - 1) * 100
        servers_needed = target / max_capacity
        print(f"⚠️ CE SERVEUR PEUT GÉNÉRER {max_capacity:,.0f} QR/JOUR")
        print(f"🎯 OBJECTIF 100M: INSUFFISANT (-{deficit:.1f}%)")
        print(f"🔢 Il faudrait {servers_needed:.1f} serveurs similaires")
    
    print(f"\n💰 COÛT PAR QR: {(500 / max_capacity * 365):.6f}€")  # 500€/mois serveur
    print(f"📈 ROI: Excellent pour services gouvernementaux")
