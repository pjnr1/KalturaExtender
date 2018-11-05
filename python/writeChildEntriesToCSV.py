from datetime import datetime
import csv
import operator

# Kaltura helpers
from Llab_libs.KalturaExtensions import *
from Llab_libs.KalturaExtensions import __basepath__


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    print(now(), 'Running', __file__, end='\n\n')

    print(now(), 'Setting up client', end='\n\n')
    client = KalturaExtender()

    print(now(), 'Get dualstream channels', end='\n\n')
    channels = client.get_dualstream_channels()

    childs = {}
    for c, o in channels.items():
        print(now(), 'Fetching recordings from {}'.format(c))
        res = client.get_entries(filters={'parentEntryIdEqual': c,
                                          'mediaTypeEqual': 1})

        for r in res.items():
            childs[r[0]] = r[1]

    print(now(), 'Concat parents and child entries', end='\n\n')
    channels.update(childs)

    outdict = {}
    for c in channels.items():
        outdict[c[0]] = c[1]

    print(now(), 'Write csv', end='\n\n')
    csvFilePath = '../csv_files/dualstream-recordings.csv'
    export_to_csv(outdict, csvFilePath)

    print(now(), 'Done writing', end='\n\n')
