#!/usr/bin/env python3
"""
Exemples de code d'implémentation - Plateforme QR Congo
Code samples pour les microservices principaux
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import hashlib
import qrcode
import uuid
import json
import jwt
import redis
from celery import Celery
import asyncio
from PIL import Image
import io
import base64

# ========== MODÈLES DE DONNÉES ==========

Base = declarative_base()

class Certification(Base):
    """Modèle certification OCC"""
    __tablename__ = "certifications"
    
    id = Column(String, primary_key=True)
    company_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    product_category = Column(String, nullable=False)
    certification_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    occ_officer = Column(String, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    """Modèle commande estampilles"""
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True)
    certification_id = Column(String, nullable=False)
    company_id = Column(String, nullable=False)
    estampilleur_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, paid, generating, ready, completed
    payment_status = Column(String, default="unpaid")
    created_at = Column(DateTime, default=datetime.utcnow)
    generation_task_id = Column(String, nullable=True)

class QRCode(Base):
    """Modèle QR code généré"""
    __tablename__ = "qr_codes"
    
    id = Column(String, primary_key=True)
    order_id = Column(String, nullable=False)
    qr_data = Column(String, nullable=False)
    security_hash = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    status = Column(String, default="generated")  # generated, distributed, printed, scanned
    created_at = Column(DateTime, default=datetime.utcnow)

# ========== SCHEMAS PYDANTIC ==========

class OrderCreateRequest(BaseModel):
    certification_id: str = Field(..., description="ID certification OCC")
    quantity: int = Field(..., ge=1, le=1000000, description="Quantité estampilles")
    estampilleur_id: str = Field(..., description="ID estampilleur agréé")
    delivery_format: str = Field("png", description="Format: png, svg, pdf, csv")
    batch_size: int = Field(10000, description="Taille des lots")

class QRGenerationTask(BaseModel):
    task_id: str
    order_id: str
    status: str
    progress: Dict
    estimated_completion: Optional[datetime]
    download_url: Optional[str]

class QRVerificationRequest(BaseModel):
    qr_data: str = Field(..., description="Contenu QR code scanné")
    scan_location: Optional[str] = None
    device_info: Optional[str] = None

# ========== SERVICE AUTHENTICATION ==========

class AuthService:
    """Service d'authentification gouvernementale"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    def create_jwt_token(self, user_id: str, role: str, permissions: List[str]) -> str:
        """Crée un token JWT avec rôles et permissions"""
        payload = {
            'user_id': user_id,
            'role': role,
            'permissions': permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Dict:
        """Vérifie et décode un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            # Vérifier si le token n'est pas en blacklist
            if self.redis_client.get(f"blacklist:{token}"):
                raise HTTPException(status_code=401, detail="Token invalidated")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

# ========== QR GENERATION SERVICE ==========

class QRGenerationService:
    """Service de génération massive de QR codes"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
        
    def generate_secure_qr_data(self, order: Order, certification: Certification, sequence: int) -> Dict:
        """Génère les données sécurisées pour un QR code"""
        qr_id = f"gov-cg-{datetime.now().strftime('%Y%m%d')}-{sequence:08d}"
        
        # Données QR compactes
        qr_data = {
            'gov': 'cg',  # Congo
            'id': qr_id,
            'cert': certification.id,
            'prod': certification.product_name[:20],  # Tronqué pour taille
            'comp': order.company_id,
            'exp': certification.expiry_date.strftime('%Y%m%d'),
            'seq': sequence,
            'v': '1.0'
        }
        
        # Hash de sécurité
        data_string = json.dumps(qr_data, sort_keys=True)
        security_hash = hashlib.sha256(
            f"{data_string}:{order.id}:CONGO_SECRET_KEY".encode()
        ).hexdigest()[:16]
        
        qr_data['hash'] = security_hash
        
        return {
            'qr_id': qr_id,
            'qr_data': json.dumps(qr_data, separators=(',', ':')),
            'security_hash': security_hash
        }
    
    def create_qr_image(self, qr_data: str, format: str = 'png') -> bytes:
        """Crée l'image QR code"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        if format.lower() == 'png':
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
        elif format.lower() == 'svg':
            # Pour SVG, utiliser qrcode[pil] avec factory
            import qrcode.image.svg
            factory = qrcode.image.svg.SvgPathImage
            img = qr.make_image(image_factory=factory)
            return str(img).encode()
        
        raise ValueError(f"Format {format} non supporté")

# ========== CELERY TASKS ==========

# Configuration Celery
celery_app = Celery(
    'qr_generator',
    broker='redis://localhost:6379/2',
    backend='redis://localhost:6379/2'
)

@celery_app.task(bind=True)
def generate_qr_batch(self, order_id: str, start_sequence: int, batch_size: int):
    """Tâche Celery pour génération d'un lot de QR codes"""
    try:
        # Simulation récupération order et certification
        # En réalité : récupération depuis base de données
        
        qr_service = QRGenerationService()
        generated_qrs = []
        
        for i in range(batch_size):
            sequence = start_sequence + i
            
            # Génération QR data (simulation)
            qr_info = qr_service.generate_secure_qr_data(
                order=None,  # À remplacer par vraie order
                certification=None,  # À remplacer par vraie certification
                sequence=sequence
            )
            
            # Génération image
            qr_image = qr_service.create_qr_image(qr_info['qr_data'])
            
            # Sauvegarde (simulation)
            generated_qrs.append({
                'qr_id': qr_info['qr_id'],
                'qr_data': qr_info['qr_data'],
                'image_base64': base64.b64encode(qr_image).decode()
            })
            
            # Mise à jour progression
            progress = (i + 1) / batch_size * 100
            self.update_state(
                state='PROGRESS',
                meta={'current': i + 1, 'total': batch_size, 'percentage': progress}
            )
        
        return {
            'status': 'completed',
            'generated_count': len(generated_qrs),
            'qr_codes': generated_qrs
        }
        
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise

# ========== API MICROSERVICES ==========

# API Order Service
order_app = FastAPI(title="Order Service", version="1.0.0")
security = HTTPBearer()

@order_app.post("/orders", response_model=Dict)
async def create_order(
    order_request: OrderCreateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Créer une nouvelle commande d'estampilles"""
    
    # Vérification authentification
    auth_service = AuthService("SECRET_KEY")
    user_info = auth_service.verify_token(credentials.credentials)
    
    # Vérification permissions
    if 'orders.create' not in user_info['permissions']:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Validation certification existe
    # certification = get_certification(order_request.certification_id)
    
    # Création commande
    order_id = f"ord-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    
    # Simulation sauvegarde base de données
    order_data = {
        'id': order_id,
        'certification_id': order_request.certification_id,
        'company_id': user_info['user_id'],
        'estampilleur_id': order_request.estampilleur_id,
        'quantity': order_request.quantity,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    }
    
    return {
        'order_id': order_id,
        'status': 'created',
        'message': 'Commande créée avec succès. En attente de paiement.',
        'payment_url': f"/payments/{order_id}"
    }

@order_app.post("/orders/{order_id}/generate")
async def trigger_qr_generation(
    order_id: str,
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Déclencher la génération QR après paiement validé"""
    
    # Vérification order existe et payée
    # order = get_order(order_id)
    # if order.payment_status != 'paid':
    #     raise HTTPException(status_code=400, detail="Order not paid")
    
    # Lancement génération asynchrone
    task = generate_qr_batch.delay(
        order_id=order_id,
        start_sequence=1,
        batch_size=10000  # Premier lot de 10K
    )
    
    return {
        'task_id': task.id,
        'status': 'started',
        'status_url': f"/orders/{order_id}/status/{task.id}",
        'estimated_completion': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    }

# API Verification Service
verification_app = FastAPI(title="Verification Service", version="1.0.0")

@verification_app.post("/verify")
async def verify_qr_code(verification_request: QRVerificationRequest):
    """Vérification publique d'un QR code par un consommateur"""
    
    try:
        # Parse QR data
        qr_data = json.loads(verification_request.qr_data)
        
        # Vérifications de base
        if qr_data.get('gov') != 'cg':
            raise HTTPException(status_code=400, detail="QR code non congolais")
        
        # Vérification hash de sécurité
        qr_id = qr_data.get('id')
        stored_hash = qr_data.get('hash')
        
        # Recalcul hash pour vérification
        temp_data = qr_data.copy()
        del temp_data['hash']
        data_string = json.dumps(temp_data, sort_keys=True)
        calculated_hash = hashlib.sha256(
            f"{data_string}:ORDER_ID:CONGO_SECRET_KEY".encode()
        ).hexdigest()[:16]
        
        if stored_hash != calculated_hash:
            # Log tentative de fraude
            return {
                'valid': False,
                'reason': 'security_hash_invalid',
                'message': 'QR code potentially counterfeit'
            }
        
        # Vérification en base de données
        # qr_record = get_qr_from_db(qr_id)
        
        # Vérification expiration
        expiry_str = qr_data.get('exp')
        expiry_date = datetime.strptime(expiry_str, '%Y%m%d')
        
        if expiry_date < datetime.now():
            return {
                'valid': False,
                'reason': 'expired',
                'message': 'Certification expired'
            }
        
        # Log du scan pour analytics
        # log_qr_scan(qr_id, verification_request.scan_location)
        
        # QR valide - retourner infos produit
        return {
            'valid': True,
            'product_info': {
                'name': qr_data.get('prod'),
                'certification_id': qr_data.get('cert'),
                'company_id': qr_data.get('comp'),
                'expiry_date': expiry_str,
                'verification_date': datetime.utcnow().isoformat()
            },
            'verification_id': f"ver-{uuid.uuid4().hex[:8]}",
            'redirect_url': f"https://occ.gov.cg/product/{qr_data.get('cert')}"
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid QR code format")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Verification error")

# ========== DISTRIBUTION SERVICE ==========

class DistributionService:
    """Service de distribution vers estampilleurs"""
    
    def __init__(self):
        self.formats_supported = ['png', 'svg', 'pdf', 'csv', 'json', 'zpl']
    
    async def prepare_download_package(self, order_id: str, format: str) -> Dict:
        """Prépare le package de téléchargement pour estampilleur"""
        
        # Récupération QR codes de la commande
        # qr_codes = get_qr_codes_by_order(order_id)
        
        if format == 'csv':
            # Format CSV avec liens images
            csv_content = self.generate_csv_format(order_id)
            return {
                'type': 'csv',
                'filename': f'qr_codes_{order_id}.csv',
                'content': csv_content
            }
        
        elif format == 'json':
            # Format JSON structuré
            json_content = self.generate_json_format(order_id)
            return {
                'type': 'json',
                'filename': f'qr_codes_{order_id}.json',
                'content': json_content
            }
        
        elif format in ['png', 'svg']:
            # Package ZIP avec images
            zip_content = self.generate_image_package(order_id, format)
            return {
                'type': 'zip',
                'filename': f'qr_images_{order_id}.zip',
                'content': zip_content
            }
    
    def generate_csv_format(self, order_id: str) -> str:
        """Génère fichier CSV pour estampilleur"""
        csv_lines = [
            'qr_id,qr_data,image_url,security_hash,sequence'
        ]
        
        # Simulation données
        for i in range(10):  # Exemple avec 10 QR
            csv_lines.append(
                f"gov-cg-20241201-{i:08d},"
                f'"{{"gov":"cg","id":"gov-cg-20241201-{i:08d}"}}","'
                f"https://storage.occ.gov.cg/qr/{order_id}/{i:08d}.png,"
                f"abc123def456,"
                f"{i+1}"
            )
        
        return '\n'.join(csv_lines)
    
    def generate_json_format(self, order_id: str) -> str:
        """Génère fichier JSON structuré"""
        data = {
            'order_id': order_id,
            'generated_at': datetime.utcnow().isoformat(),
            'total_count': 1000,  # Exemple
            'qr_codes': []
        }
        
        # Simulation données
        for i in range(10):
            data['qr_codes'].append({
                'qr_id': f"gov-cg-20241201-{i:08d}",
                'sequence': i + 1,
                'qr_data': json.dumps({
                    'gov': 'cg',
                    'id': f"gov-cg-20241201-{i:08d}",
                    'cert': 'cert-123',
                    'hash': 'abc123'
                }),
                'image_base64': 'iVBORw0KGgoAAAANSUhEUgAA...',  # Base64 image
                'security_hash': 'abc123def456'
            })
        
        return json.dumps(data, indent=2)

if __name__ == "__main__":
    print("📝 EXEMPLES DE CODE D'IMPLÉMENTATION")
    print("=" * 50)
    
    print("✅ Modèles de données définis (SQLAlchemy)")
    print("✅ Services d'authentification (JWT + Redis)")
    print("✅ Service génération QR codes (qrcode + Pillow)")
    print("✅ Tâches Celery pour parallélisation")
    print("✅ APIs FastAPI (Order + Verification)")
    print("✅ Service de distribution multi-format")
    
    print("\n🚀 PRÊT POUR DÉVELOPPEMENT !")
    print("Structure de code complète pour démarrage projet")
