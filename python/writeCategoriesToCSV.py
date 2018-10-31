from datetime import datetime
import random

# Kaltura helpers
from Llab_libs.KalturaExtensions import *


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    print(now(), 'Running', __file__)
    print()

    print(now(), 'Setting up client')
    client = KalturaExtender()
    print()

    print(now(), 'Get all categories')
    path = '../csv_files/cats.csv'
    l = client.get_categories()
    print()

    print(now(), 'Write categories to csv')
    v = vars(l[random.choice(list(l.keys()))])
    exportToCsv(l, path, specificVariables=v)
    print()

    print(now(), 'done')
