"""
This file is kept as a playground for all minor non-automatic calls to the Kaltura API
"""
from Llab_libs.KalturaExtensions import *
import json
import time
from Llab_libs.meta_helper import *
import requests


def download_file(url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    total_bytes = int(r.raw.length_remaining / 1048576)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                print('{} / {}'.format(int(r.raw._fp_bytes_read / 1048576), total_bytes))
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_filename


if __name__ == '__main__':
    client = KalturaExtender(log=True, log_level='all', errormail=False)
    # client.get_updated_entries(int(datetime.timestamp(datetime(year=2019, month=1, day=11, hour=8, minute=30, second=59))))
    # res = client.get_updated_since_last_run()

    res = client.get_entries_by_user('jectli@llab.dtu.dk')
    for key, item in res.items():
        if key == '0_9b9fxnfw':
            download_file(item.downloadUrl)
            print(key, item.name, item.downloadUrl)

    # mixEntry = client.create_mix_entry('Test mixEntry')

    #res = client.append_mix_entry(mixEntryId='0_ilr98rvh', mediaEntryId='0_te6e8t2c')
    #printKalturaObject(client.get_entry('0_ilr98rvh', 'mixing'))

    # print('something', res)
    # client.update_entry(entryId='0_sggjsk73', updates={'categoriesIds': '186579'})
    # client.update_entry(entryId='0_07bwdxgs', updates={'parentEntryId': '0_sggjsk73'})
    # client.update_dual_user_list()
    # client.update_dual_user_ownerships()
    # printKalturaObject(client.get_client().media.get('0_otrwgrm2'))
