# 🇨🇩 Test QR Congo sur VPS - Guide d'Installation

## 🚀 Installation Rapide

### 1. Transférer les fichiers sur votre VPS

```bash
# Sur votre machine locale
scp test_vps_setup.py install_dependencies.sh root@votre-vps:/root/

# Ou utiliser git
git clone https://github.com/votre-repo/qr-congo.git
cd qr-congo
```

### 2. Installation des dépendances

```bash
# Sur votre VPS
chmod +x install_dependencies.sh
./install_dependencies.sh
```

### 3. Activation environnement

```bash
source qr_env/bin/activate
```

### 4. Test de génération

```bash
python3 test_vps_setup.py
```

---

## 📱 Ce que vous allez voir

### 🖼️ **QR Codes Générés**
- Images PNG 600x600 pixels, 300 DPI
- Données gouvernementales Congo réalistes
- Hash de sécurité SHA-256
- Format compatible estampilleurs

### 📄 **Fichiers de Sortie**
```
qr_test_output/
├── images/              # Images QR codes
│   ├── gov-cg-20241201-00000001.png
│   ├── gov-cg-20241201-00000002.png
│   └── ...
├── csv/                 # Export CSV pour estampilleurs
│   └── qr_codes_export.csv
├── json/                # Export JSON structuré
│   └── qr_codes_export.json
├── reports/             # Rapport de performance
│   └── test_report.txt
└── qr_viewer.html       # Visualiseur web
```

### 🌐 **Visualiseur Web**
- Ouvrir `qr_test_output/qr_viewer.html` dans navigateur
- Voir tous les QR codes générés
- Informations détaillées par QR
- Design gouvernemental Congo

---

## 📊 **Données QR Réalistes**

Chaque QR contient :
```json
{
  "gov": "cg",
  "id": "gov-cg-20241201-00000001",
  "cert": "occ-2024-000001",
  "prod": "Jus_Orange",
  "comp": "BRALIMA", 
  "exp": "20251231",
  "batch": "LOT0001",
  "ts": "20241201143052",
  "hash": "a1b2c3d4e5f6g7h8",
  "v": "1.0"
}
```

---

## 🔧 **Test de Performance**

Le script mesure automatiquement :
- **Vitesse de génération** (QR/seconde)
- **Utilisation mémoire** (KB par QR)
- **Capacité quotidienne estimée**
- **Temps total de traitement**

### Résultats attendus sur VPS standard :
- **1-5 QR/seconde** selon CPU
- **~20-50 KB par QR** en PNG
- **Capacité 86K-432K QR/jour** par core

---

## 📱 **Test avec Smartphone**

### Applications recommandées :
- **Android :** QR & Barcode Scanner
- **iPhone :** Appareil photo natif
- **Universal :** QR Code Reader

### Test de scan :
1. Ouvrir `qr_viewer.html`
2. Scanner un QR avec smartphone
3. Vérifier que les données s'affichent
4. Valider le format JSON

---

## 🎯 **Interprétation Résultats**

### Performance Cible :
```
Objectif Congo: 100M QR/jour
= 1,157 QR/seconde
= Besoin de ~200-1000 cores selon performance VPS
```

### Estimation pour votre VPS :
- **Si 2 QR/sec :** ~500 serveurs nécessaires
- **Si 10 QR/sec :** ~100 serveurs nécessaires  
- **Si 50 QR/sec :** ~20 serveurs nécessaires

---

## 🔍 **Validation Technique**

### ✅ **Vérifications à faire :**

1. **Images QR :**
   - [ ] Résolution 600x600 pixels
   - [ ] Scannables avec smartphone
   - [ ] Taille ~20-50 KB
   - [ ] Format PNG correct

2. **Données JSON :**
   - [ ] Format gouvernemental respect
   - [ ] Hash de sécurité présent
   - [ ] Encodage UTF-8 correct
   - [ ] Structure valide

3. **Performance :**
   - [ ] Vitesse acceptable (>1 QR/sec)
   - [ ] Mémoire stable
   - [ ] Pas d'erreurs
   - [ ] Temps de réponse <10s pour 10 QR

4. **Exports :**
   - [ ] CSV lisible Excel
   - [ ] JSON valide
   - [ ] HTML s'affiche correctement
   - [ ] Rapport complet

---

## 🚨 **Dépannage**

### Erreur "Module not found" :
```bash
source qr_env/bin/activate
pip install qrcode[pil] Pillow
```

### Erreur Pillow :
```bash
sudo apt install libjpeg-dev zlib1g-dev libpng-dev
pip install --upgrade Pillow
```

### Performance lente :
```bash
# Vérifier CPU
nproc
top

# Optimiser pour votre VPS
python3 test_vps_setup.py
# Entrer un nombre plus petit (5-10 QR)
```

### QR non scannables :
- Vérifier résolution smartphone
- Augmenter luminosité écran
- Essayer scanner différent
- Vérifier taille QR (minimum 2cm)

---

## 🎉 **Prochaines Étapes**

Après test réussi :

1. **Optimisation :** Parallélisation multiprocessing
2. **API :** FastAPI pour interface web
3. **Base données :** PostgreSQL pour stockage
4. **Distribution :** SFTP pour estampilleurs
5. **Monitoring :** Métriques temps réel

---

## 📞 **Support**

En cas de problème :
- Vérifier logs dans terminal
- Envoyer fichier `test_report.txt`
- Indiquer système d'exploitation VPS
- Joindre capture d'écran erreurs

**Test optimisé pour validation concept avant production ! 🚀**
