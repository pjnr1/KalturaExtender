from datetime import datetime
import random

# Kaltura helpers
from Llab_libs.KalturaExtensions import *


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    client = KalturaExtender(log=True, log_level=1, errormail=False)
    path = '../csv_files/cats.csv'
    l = client.get_categories()
    v = vars(l[random.choice(list(l.keys()))])
    export_to_csv(l, path, specificVariables=v)
