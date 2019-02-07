"""
This file is kept as a playground for all minor non-automatic calls to the Kaltura API
"""
from Llab_libs.KalturaExtensions import *
import json
import time

if __name__ == '__main__':
    client = KalturaExtender(log_level='all')
    #client.update_entry(entryId='0_sggjsk73', updates={'categoriesIds': '186579'})
    #client.update_entry(entryId='0_07bwdxgs', updates={'parentEntryId': '0_sggjsk73'})
    #client.update_dual_user_list()
   # client.update_dual_user_ownerships()
    #printKalturaObject(client.get_client().media.get('0_otrwgrm2'))
    #res = client.get_entries(filters={'categoriesIdsMatchAnd': '207230'},
    #                         printResult=True,
    #                         specificVariables=['id', 'name', 'entitledUsersEdit', 'userId'])
    #print(res)
    res = client.get_entries(filters={'categoriesIdsMatchAnd': '185137'})
    for i, r in res.items():
        print(i, r.name, r.description)

    res = client.set_parent('', '0_tealz2sj')
    res2 = client.get_entry(entryId='0_y8stg2zx')
    res3 = client.get_entry(entryId='0_tealz2sj')
    client.update_entry(entryId='0_tealz2sj', updates={'displayInSearch':1})
    for k, i in res2.__dict__.items():
        print(k, res2.__dict__[k], res3.__dict__[k])
    exit(0)


