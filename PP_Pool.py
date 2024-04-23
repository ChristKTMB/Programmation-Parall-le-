import os
import time
import psutil
from multiprocessing import Pool
import matplotlib.pyplot as plt
from PIL import Image

def convertir_en_noir_blanc(chemin_image):
    image = Image.open(chemin_image)
    image_noir_blanc = image.convert("L")

    dossier_convert = "img_convert"
    if not os.path.exists(dossier_convert):
        os.makedirs(dossier_convert)

    nom_image = os.path.basename(chemin_image)
    chemin_image_noir_blanc = os.path.join(dossier_convert, nom_image.replace(".", "_noir_blanc."))
    image_noir_blanc.save(chemin_image_noir_blanc)

def traiter_images_par_pool(liste_chemins_images, num_processes):
    with Pool(processes=num_processes) as pool:
        temps_debut_total = time.time()
        pool.map(convertir_en_noir_blanc, liste_chemins_images)
        temps_fin_total = time.time()
        temps_ecoule_total = temps_fin_total - temps_debut_total
    return round(temps_ecoule_total, 2)

if __name__ == '__main__':
    dossier_images = "data/cars"
    chemins_images = [os.path.join(dossier_images, fichier) for fichier in os.listdir(dossier_images) if fichier.endswith((".jpg", ".png", ".bmp"))]

    nb_processus = [1, 2, 3, 4, 5, 6, 7, 8]

    temps_total_par_processus = []
    pourcentages_cpu = []
    pourcentages_ram = []

    for nb_procs in nb_processus:
        print(f"Traitement avec {nb_procs} processus...")
        print("______________________________")
        resultat = traiter_images_par_pool(chemins_images, nb_procs)
        print(f"- Temps du traitement = {resultat} s\n")
        temps_total_par_processus.append(resultat)
        pourcentages_cpu.append(psutil.cpu_percent())
        pourcentages_ram.append(psutil.virtual_memory().percent)

    # Afficher les temps total écoulés pour chaque nombre de processus sous forme de graphique à barres colorées
    plt.figure(figsize=(10, 6))
    plt.bar(nb_processus, temps_total_par_processus, color=['red', 'green', 'blue', 'orange', 'purple', 'cyan', 'magenta', 'yellow'])
    plt.xlabel('Nombre de processus')
    plt.ylabel('Temps total écoulé (secondes)')
    plt.title('Temps total écoulé pour différents nombres de processus')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    
    axs[0].pie(pourcentages_cpu, labels=nb_processus, autopct='%1.1f%%', startangle=140)
    axs[0].set_title('Répartition CPU pour différents nombres de processus')
    
    axs[1].pie(pourcentages_ram, labels=nb_processus, autopct='%1.1f%%', startangle=140)
    axs[1].set_title('Répartition RAM pour différents nombres de processus')
    
    plt.show()