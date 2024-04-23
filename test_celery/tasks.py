from __future__ import absolute_import
from test_celery.celery import app
import logging
import time

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) 

@app.task
def longtime_add(x, y):
    logger.info(f"Tâche add({x}, {y}) démarrée")
    result = x + y
    logger.info(f"Tâche add({x}, {y}) terminée avec succès. Résultat : {result}")
    return result