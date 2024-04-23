import os
import time
import psutil
from multiprocessing import Process
import matplotlib.pyplot as plt
from PIL import Image

def convertir_en_noir_blanc(chemins_images):
    for chemin_image in chemins_images:
        image = Image.open(chemin_image)
        image_noir_blanc = image.convert("L")

        dossier_convert = "img_convert"
        if not os.path.exists(dossier_convert):
            os.makedirs(dossier_convert)

        nom_image = os.path.basename(chemin_image)
        chemin_image_noir_blanc = os.path.join(dossier_convert, nom_image.replace(".", "_noir_blanc."))
        image_noir_blanc.save(chemin_image_noir_blanc)

def traiter_images_par_lot(liste_chemins_images, num_processes):

    taille_lot_initial = len(liste_chemins_images) // num_processes

    # Créer les lots initiaux avec la taille définie
    lots = [liste_chemins_images[i:i+taille_lot_initial] for i in range(0, taille_lot_initial * (num_processes - 1), taille_lot_initial)]

    # Ajouter le reste des images au dernier lot
    dernier_lot = liste_chemins_images[taille_lot_initial * (num_processes - 1):]
    lots.append(dernier_lot)

    processes = []
    temps_debut_processus = [] 
    temps_total_processus = [] 

    for i, lot in enumerate(lots):
        temps_debut_processus.append(time.time()) 
        process = Process(target=convertir_en_noir_blanc, args=(lot,))
        process.start()
        processes.append(process)
        print(f"Nombre des images traiter lot {i + 1} = {len(lot)} images")

    for i, process in enumerate(processes):
        process.join()
        temps_debut = temps_debut_processus[i]
        temps_fin = time.time()
        temps_processus = temps_fin - temps_debut
        temps_total_processus.append(temps_processus)
        # print(f"Durée du processus {i+1} : {round(temps_processus, 2)} secondes")

    return round(sum(temps_total_processus), 2)


if __name__ == '__main__':
    dossier_images = "data/cars"
    # Liste de chemins d'images
    chemins_images = [os.path.join(dossier_images, fichier) for fichier in os.listdir(dossier_images) if fichier.endswith((".jpg", ".png", ".bmp"))]

    nb_processus = [1, 2, 3, 4, 5, 6, 7, 8]

    temps_total_par_processus = []
    pourcentages_cpu = []
    pourcentages_ram = []

    for nb_procs in nb_processus:
        print(f"Traitement avec {nb_procs} processus...")
        print("______________________________")
        resultat = traiter_images_par_lot(chemins_images, nb_procs)
        print(f"- Temps du traitement = {resultat} s\n")
        temps_total_par_processus.append(resultat)
        pourcentages_cpu.append(psutil.cpu_percent())
        pourcentages_ram.append(psutil.virtual_memory().percent)

    # # Afficher les temps total écoulés pour chaque nombre de processus sous forme de graphique à barres colorées
    plt.figure(figsize=(10, 6))
    plt.bar(nb_processus, temps_total_par_processus, color=['red', 'green', 'blue', 'orange', 'purple', 'cyan', 'magenta', 'yellow'])
    for i in range(len(nb_processus)):
        plt.text(nb_processus[i], temps_total_par_processus[i], f"{temps_total_par_processus[i]}s")
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

    # Afficher les temps total écoulés pour chaque nombre de processus sous forme de graphique à barres colorées
    # fig, ax1 = plt.subplots(figsize=(10, 6))

    # color = 'tab:red'
    # ax1.set_xlabel('Nombre de processus')
    # ax1.set_ylabel('Temps total écoulé (secondes)', color=color)
    # ax1.bar(nb_processus, temps_total_par_processus, color=color)
    # ax1.tick_params(axis='y', labelcolor=color)

    # ax2 = ax1.twinx()  

    # color = 'tab:blue'
    # ax2.set_ylabel('Pourcentage CPU/RAM', color=color)  
    # ax2.plot(nb_processus, pourcentages_cpu, color=color, linestyle='--', label='CPU (%)')
    # ax2.plot(nb_processus, pourcentages_ram, color=color, linestyle='-', label='RAM (%)')
    # ax2.tick_params(axis='y', labelcolor=color)

    # fig.tight_layout()  
    # plt.title('Temps total écoulé et pourcentage CPU/RAM pour différents nombres de processus')
    # plt.legend()
    # plt.show()


