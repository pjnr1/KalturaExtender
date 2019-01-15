"""
This file is kept as a playground for all minor non-automatic calls to the Kaltura API
"""
from Llab_libs.KalturaExtensions import *
import json
import time
from Llab_libs.meta_helper import *


if __name__ == '__main__':
    client = KalturaExtender(log=True, log_level='all', errormail=False)
    # client.get_updated_entries(int(datetime.timestamp(datetime(year=2019, month=1, day=11, hour=8, minute=30, second=59))))
    res = client.get_updated_since_last_run()
    for key, item in res.items():
        print(key, item.name)

    # mixEntry = client.create_mix_entry('Test mixEntry')

    #res = client.append_mix_entry(mixEntryId='0_ilr98rvh', mediaEntryId='0_te6e8t2c')
    printKalturaObject(client.get_entry('0_ilr98rvh', 'mixing'))

    print('something', res)
    # client.update_entry(entryId='0_sggjsk73', updates={'categoriesIds': '186579'})
    # client.update_entry(entryId='0_07bwdxgs', updates={'parentEntryId': '0_sggjsk73'})
    # client.update_dual_user_list()
    # client.update_dual_user_ownerships()
    # printKalturaObject(client.get_client().media.get('0_otrwgrm2'))
