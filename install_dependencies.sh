#!/bin/bash
# Installation des dépendances pour test QR Congo sur VPS

echo "🇨🇩 Installation dépendances QR Congo - VPS Setup"
echo "=================================================="

# Mise à jour système
echo "📦 Mise à jour système..."
sudo apt update && sudo apt upgrade -y

# Installation Python et pip
echo "🐍 Installation Python 3.11..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Installation des dépendances système pour Pillow
echo "🖼️ Installation dépendances images..."
sudo apt install -y libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev

# Création environnement virtuel
echo "📁 Création environnement virtuel..."
python3 -m venv qr_env
source qr_env/bin/activate

# Installation packages Python
echo "📚 Installation packages Python..."
pip install --upgrade pip

# Packages essentiels pour QR
pip install qrcode[pil]==7.4.2
pip install Pillow==10.1.0

# Packages optionnels pour version complète
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install redis==5.0.1
pip install celery==5.3.4
pip install psutil==5.9.6

# Vérification installation
echo "✅ Vérification installation..."
python3 -c "import qrcode; import PIL; print('QR code libs OK!')"

echo ""
echo "🎉 INSTALLATION TERMINÉE!"
echo "=========================================="
echo "Pour activer l'environnement:"
echo "source qr_env/bin/activate"
echo ""
echo "Pour tester:"
echo "python3 test_vps_setup.py"
echo ""
echo "📱 Assurez-vous d'avoir un smartphone pour scanner les QR!"
