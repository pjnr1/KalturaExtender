from datetime import datetime
import csv
import operator

# Kaltura helpers
from Llab_libs.KalturaExtensions import *
from Llab_libs.KalturaExtensions import __basepath__


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    client = KalturaExtender(log=True, errormail=False)

    channels = client.get_dualstream_channels()

    childs = {}
    for c, o in channels.items():
        res = client.get_entries(filters={'parentEntryIdEqual': c,
                                          'mediaTypeEqual': 1})

        for r in res.items():
            childs[r[0]] = r[1]
    channels.update(childs)

    outdict = {}
    for c in channels.items():
        outdict[c[0]] = c[1]

    csvFilePath = '../csv_files/dualstream-recordings.csv'
    export_to_csv(outdict, csvFilePath)
