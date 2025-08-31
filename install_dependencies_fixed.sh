#!/bin/bash
# Installation dépendances QR Congo - Version corrigée

echo "🇨🇩 Installation QR Congo - Version Fixée"
echo "=========================================="

# Mise à jour système
echo "📦 Mise à jour système..."
sudo apt update

# Installation Python et dépendances système
echo "🐍 Installation Python et dépendances..."
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev

# Création environnement virtuel
echo "📁 Création environnement virtuel..."
python3 -m venv qr_env

# Activation
echo "⚡ Activation environnement..."
source qr_env/bin/activate

# Mise à jour pip
echo "🔧 Mise à jour pip..."
pip install --upgrade pip

# Option 1: Installation minimale pour test
echo "🚀 Option 1 - Installation minimale (test QR)..."
echo "pip install -r requirements_test_vps.txt"

# Option 2: Installation production avec versions compatibles
echo "🏭 Option 2 - Installation production (versions fixées)..."
echo "pip install -r requirements_production_fixed.txt"

# Test installation minimale par défaut
echo "📦 Installation automatique version test..."
pip install qrcode[pil]==7.4.2 Pillow==10.1.0 psutil==5.9.6

# Vérification
echo "✅ Vérification installation..."
python3 -c "
import qrcode
import PIL
print('✅ QR code libraries OK!')
print('📱 Prêt pour génération QR')
"

echo ""
echo "🎉 INSTALLATION TERMINÉE!"
echo "========================"
echo ""
echo "🔧 Commandes disponibles:"
echo "source qr_env/bin/activate  # Activer environnement"
echo "python3 test_simple.py      # Test basique"
echo "python3 test_vps_setup.py   # Test complet"
echo ""
echo "💡 Pour installation complète production:"
echo "pip install -r requirements_production_fixed.txt"
echo ""
echo "🐛 En cas d'erreur dépendances:"
echo "pip install --upgrade pip setuptools wheel"
