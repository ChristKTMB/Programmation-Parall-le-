import os
import time
from with_celery.celery import convertir_en_noir_blanc

if __name__ == '__main__':
    dossier_images = "data/cars"
    chemins_images = [os.path.join(dossier_images, fichier) for fichier in os.listdir(dossier_images) if fichier.endswith((".jpg", ".png", ".bmp"))]

    debut = time.time()
    for chemin_image in chemins_images:
        convertir_en_noir_blanc.delay(chemin_image)
    fin = time.time()

    temps_total = fin - debut
    print(f"Temps total écoulé pour le traitement de {len(chemins_images)} images : {temps_total} secondes.")