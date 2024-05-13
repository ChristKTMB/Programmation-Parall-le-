from celery import Celery
from PIL import Image
import os

app = Celery('with_celery',
             broker='amqp://guest:guest@localhost/',
             backend='rpc://')

@app.task
def convertir_en_noir_blanc(chemin_image):
    image = Image.open(chemin_image)
    image_noir_blanc = image.convert("L")

    dossier_convert = "img_convert"
    if not os.path.exists(dossier_convert):
        os.makedirs(dossier_convert)

    nom_image = os.path.basename(chemin_image)
    chemin_image_noir_blanc = os.path.join(dossier_convert, nom_image.replace(".", "_noir_blanc."))
    image_noir_blanc.save(chemin_image_noir_blanc)