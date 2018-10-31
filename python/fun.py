from Llab_libs.KalturaExtensions import *
import json

if __name__ == '__main__':
    client = KalturaExtender(log=True, errormail=True)
    client.update_dual_user_list()
    client.update_dual_user_ownerships()
    printKalturaObject(client.get_client().media.get('0_otrwgrm2'))
