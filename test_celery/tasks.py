from __future__ import absolute_import
from test_celery.celery import app
import time


@app.task
def longtime_add(x, y):
    time.sleep(5)
    return x + y