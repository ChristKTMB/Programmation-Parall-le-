import os
import time
from PIL import Image
import matplotlib.pyplot as plt
import psutil

def convertir_en_noir_blanc(chemin_image):
    image = Image.open(chemin_image)
    image_noir_blanc = image.convert("L")

    # Créer le dossier img_convert s'il n'existe pas
    dossier_convert = "img_convert"
    if not os.path.exists(dossier_convert):
        os.makedirs(dossier_convert)

    # Enregistrer l'image convertie dans le dossier img_convert
    nom_image = os.path.basename(chemin_image)
    chemin_image_noir_blanc = os.path.join(dossier_convert, nom_image.replace(".", "_noir_blanc."))
    image_noir_blanc.save(chemin_image_noir_blanc)

    # image_noir_blanc.show()

dossier_images = "data/cars"

temps_debut = time.time()

for fichier in os.listdir(dossier_images):
    if fichier.endswith(".jpg") or fichier.endswith(".png") or fichier.endswith(".bmp"):
        # Chemin complet de l'image
        chemin_image = os.path.join(dossier_images, fichier)
        # Convertir l'image en noir et blanc
        convertir_en_noir_blanc(chemin_image)

cpu_usage = psutil.cpu_percent()
ram_usage = psutil.virtual_memory().percent
temps_fin = time.time()

temps_ecoule = temps_fin - temps_debut
print(f"Temps écoulé : {temps_ecoule} s")
print(f"Utilisation du processeur pendant l'execution : {cpu_usage}%")
print(f"Utilisation de la RAM pendant l'execution : {ram_usage}%")

# Afficher les informations sur l'utilisation du processeur et de la RAM sous forme de graphique
plt.figure(figsize=(10, 6))
plt.plot([1], [ cpu_usage], marker='o', linestyle='')
plt.plot([1], [ ram_usage], marker='o', linestyle='')
plt.xticks([1], ['Fin'])
plt.xlabel('Temps')
plt.ylabel('Pourcentage d\'utilisation')
plt.title('Utilisation du processeur et de la RAM')
plt.legend(['CPU', 'RAM'])
plt.grid(True)
plt.tight_layout()
plt.show()