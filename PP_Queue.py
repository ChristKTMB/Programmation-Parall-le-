import os
import time
from multiprocessing import Process, Queue
import matplotlib.pyplot as plt
from PIL import Image

def convertir_en_noir_blanc(chemins_images, queue):
    temps_debut_conversion = time.time()
    for chemin_image in chemins_images:
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
        
        queue.put(chemin_image_noir_blanc)  # Ajouter le chemin de l'image traitée à la queue

    temps_fin_conversion = time.time()
    temps_conversion = temps_fin_conversion - temps_debut_conversion
    return temps_conversion

def traiter_images_par_queue(liste_chemins_images, num_processes):
    queue = Queue()  # Créer une file d'attente pour stocker les chemins des images traitées
    processes = []   # Liste pour stocker les processus

    # Diviser la liste de chemins d'images en lots pour chaque processus
    taille_lot = len(liste_chemins_images) // num_processes
    lots = [liste_chemins_images[i:i+taille_lot] for i in range(0, len(liste_chemins_images), taille_lot)]

    # Créer un processus pour chaque lot d'images
    for lot in lots:
        process = Process(target=convertir_en_noir_blanc, args=(lot, queue))
        process.start()
        processes.append(process)

    # Attendre que tous les processus se terminent
    for process in processes:
        process.join()

    # Récupérer les chemins des images traitées de la queue
    chemins_images_traites = []
    while not queue.empty():
        chemins_images_traites.append(queue.get())

    return chemins_images_traites

if __name__ == '__main__':
    # Dossier contenant les images
    dossier_images = "data/human2"

    # Liste de chemins d'images
    chemins_images = [os.path.join(dossier_images, fichier) for fichier in os.listdir(dossier_images) if fichier.endswith((".jpg", ".png", ".bmp"))]

    # Nombre de processus à utiliser
    nb_processus = [1, 2, 3, 4, 5, 6, 7, 8]

    # Liste pour stocker les temps total écoulés pour chaque nombre de processus
    temps_total_par_processus = []

    # Boucle sur chaque nombre de processus
    for nb_procs in nb_processus:
        print(f"Traitement avec {nb_procs} processus")
        
        temps_debut_total = time.time()
        chemins_images_traites = traiter_images_par_queue(chemins_images, nb_procs)
        temps_fin_total = time.time()
        temps_ecoule_total = temps_fin_total - temps_debut_total

        print(f"Temps total écoulé avec {nb_procs} processus : {temps_ecoule_total} secondes")

        temps_total_par_processus.append(temps_ecoule_total)

    # Afficher les temps total écoulés pour chaque nombre de processus sous forme de graphique à barres colorées
    plt.figure(figsize=(10, 6))
    plt.bar(nb_processus, temps_total_par_processus, color=['red', 'green', 'blue', 'orange', 'purple', 'cyan', 'magenta', 'yellow'])
    plt.xlabel('Nombre de processus')
    plt.ylabel('Temps total écoulé (secondes)')
    plt.title('Temps total écoulé pour différents nombres de processus')
    plt.grid(True)
    plt.tight_layout()
    plt.show()
