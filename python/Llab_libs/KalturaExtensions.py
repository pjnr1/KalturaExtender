import csv
import re
import os
import traceback
from datetime import datetime
from Llab_libs import FuncDecorators
from Llab_libs.statics_helper import load_statics_old
from Llab_libs.mail_helper import LLabMailHelper

# Kaltura imports
from Kaltura.KalturaClient import *
from Kaltura.KalturaClient.Base import *
from Kaltura.KalturaClient.Plugins.Core import *

__basepath__ = os.path.dirname(os.path.realpath(__file__))
listOfUnixTimeStampVariables = ['createdAt', 'updatedAt', 'lastLoginTime',
                                'statusUpdatedAt', 'deletedAt', 'mediaDate',
                                'firstBroadcast', 'lastBroadcast']


def kalturaObjectValueToString(a, v):
    if v is None or v is NotImplemented:
        return None
    elif 'Kaltura' in type(v).__name__:
        return v.getValue().__str__()
    elif any(x in a for x in listOfUnixTimeStampVariables):
        return datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")
    else:
        return v.__str__()



def printKalturaObject(object, specificVariables=None, counter=None, levelOfIndent=0):
    indent = '\t' * levelOfIndent

    def printOut(a, values):
        print('{:s}{:s}:\n{:s}\t{:s}'.format(indent, a, indent, kalturaObjectValueToString(a, values)))

    if counter is not None:
        print('{:d}\t{}'.format(counter, object.id))
    else:
        if specificVariables and 'id' not in specificVariables:
            print('id: {:s}'.format(object.id))

    print('-' * 80)
    for p in vars(object).items():
        if specificVariables and p[0] not in specificVariables:
            continue

        if p[1]:
            if type(p[1]) is list:
                for a in p[1]:
                    printOut(p[0], a)
            else:
                printOut(p[0], p[1])
    print('')


def load_kaltura_statics(path):
    s = {}
    with open(path, 'r') as f:
        for line in f:
            line = re.sub("[ '\n]", '', line)
            (key, val) = line.split('=')
            s[key] = val
    return s





class KalturaExtender:
    TIMESTAMP_RANGE = 30

    client = NotImplemented
    errorMailer = NotImplemented
    ks = NotImplemented
    categoryIds = NotImplemented

    def __init__(self, log=False, errormail=False):
        s = load_statics_old(os.path.join(__basepath__, 'kaltura_statics.secret'))
        self.categoryIds = load_statics_old(os.path.join(__basepath__, 'kaltura_categoryIds'))
        # Initial API client setup
        cfg = KalturaConfiguration(s['partnerId'])
        cfg.serviceUrl = s['serviceUrl']
        self.client = KalturaClient(cfg)
        # Start session
        self.ks = self.client.session.start(s['adminSecret'], None, KalturaSessionType.ADMIN, s['partnerId'])
        self.client.setKs(self.ks)

        if errormail:
            self.errorMailer = LLabMailHelper()

    @staticmethod
    def load_kaltura_client_statics():
        s = {}
        with open(os.path.join(__basepath__, 'kaltura_statics.secret'), 'r') as f:
            for line in f:
                line = re.sub("[ '\n]", '', line)
                (key, val) = line.split('=')
                s[key] = val
        return s

    @staticmethod
    def apply_filter(filter, filters):
        if filters is not None:
            for f in filters:
                if hasattr(filter, f):
                    setattr(filter, f, filters[f])
                else:
                    print('Warning:', filters[f], 'is not a valid KalturaMediaEntryFilter() attribute')

    @staticmethod
    def comp_timestamps(t1, t2, r=0):
        t0 = t1 - t2
        t0 = abs(t0)
        return not t0 > r

    def generateThumbAndSetAsDefault(self, id, paramId=None):
        return NotImplementedError
        #
        if not paramId:
            pIds = load_statics_old("kaltura_thumbParamsIds")
            paramId = pIds['default']
        elif type(paramId) is type(str):
            pIds = load_statics_old("kaltura_thumbParamsIds")
            paramId = pIds[paramId]

        try:
            res = self.client.thumbAsset.generateByEntryId(entryId=id,
                                                           destThumbParamsId=paramId)
            self.client.thumbAsset.setAsDefault(res.id)
        except:
            print('error', id)

    def get_client(self):
        if self.client is NotImplemented:
            raise RuntimeError('KalturaExtender::client not loaded!')
        return self.client

    def get_entries(self, filters=None, entryType='media', printResult=False, specificVariables=None):
        entryFilter = KalturaMediaEntryFilter()
        self.apply_filter(entryFilter, filters)

        res = getattr(self.client, entryType).list(entryFilter)
        i = 0
        output = {}
        for entry in res.objects:
            output[entry.id] = entry

            if printResult:
                printKalturaObject(entry, specificVariables=specificVariables, counter=i)

            i += 1

        return output

    def get_live_entries(self, printResult=True, specificVariables=None):
        f = KalturaLiveEntryFilter()
        res = self.get_client().liveStream.list(f)

        i = 0
        output = {}
        for stream in res.objects:
            output[stream.id] = stream

            if printResult:
                printKalturaObject(stream, counter=i, specificVariables=specificVariables)

            i += 1

        return output

    def get_users(self, printResult=True, onlyAdmins=False, specificVariables=None):
        f = KalturaUserFilter()
        p = KalturaFilterPager()
        p.pageSize = 500
        res = self.client.user.list(f, p)
        i = 0
        output = {}
        for user in res.objects:
            if onlyAdmins and not user.isAdmin:
                continue

            output[user.id] = user

            if printResult:
                printKalturaObject(user, specificVariables=specificVariables, counter=i)

            i += 1

        return output

    def get_entries_by_user(self, username, filters=None, printResult=False, specificVariables=None):
        mediaFilter = KalturaMediaEntryFilter()
        mediaFilter.userIdEqual = username
        self.apply_filter(mediaFilter, filters)

        res = self.client.media.list(mediaFilter)

        i = 0
        output = {}
        for media in res.objects:
            output[media.id] = media

            if printResult:
                printKalturaObject(media, specificVariables=specificVariables, counter=i)

            i += 1

        return output

    def set_parent(self, parent, child, entryType='media'):
        modifierEntry = KalturaMediaEntry()
        modifierEntry.parentEntryId = parent

        return getattr(self.client, entryType).update(child, modifierEntry)

    def update_entry(self, id, updates, entryType='media', modifierEntry=KalturaMediaEntry()):
        if updates is not None:
            for u in updates:
                if hasattr(modifierEntry, u):
                    setattr(modifierEntry, u, updates[u])

        return getattr(self.client, entryType).update(id, modifierEntry)

    def delete_entry(self, id, entryType):
        return getattr(self.client, entryType).delete(id)

    # TODO:
    def get_categories(self, filters=None):
        f = KalturaCategoryFilter()
        self.apply_filter(f, filters)

        res = self.client.category.list(f,)

        i = 0
        output = {}
        for media in res.objects:
            output[media.id] = media

            i += 1

        return output

    def get_dualstream_channels(self):
        cats = load_statics_old(os.path.join(__basepath__, 'kaltura_categoryIds'))

        return self.get_entries(filters={'categoriesIdsMatchAnd': self.categoryIds['Streams'],
                                         'mediaTypeEqual': 201},
                                entryType='liveStream')

    def get_dualstream_pairs(self):
        streamEntries = self.get_dualstream_channels()

        readyEntries = {}
        for streams in streamEntries.items():
            listOfEntries = self.get_entries(filters={'rootEntryIdEqual': streams[0],
                                                      'categoriesIdsNotContains': self.categoryIds['Recordings'],
                                                      'mediaTypeEqual': 1,
                                                      'statusEqual': KalturaEntryStatus.READY})

            for entry in listOfEntries.items():
                readyEntries[entry[0]] = entry[1]

        contentEntries = []
        cameraEntries = []
        pairedEntries = []
        for entry in readyEntries.items():
            if 'Content' in entry[1].name:
                contentEntries.append(entry)
            if 'Camera' in entry[1].name:
                cameraEntries.append(entry)

        for cont in contentEntries:
            str1 = re.sub(r' [0-9]+', '', cont[1].name)
            str1 = str1.replace('Content', '').replace(' ', '')
            for cam in cameraEntries:
                str2 = cam[1].name.replace('Camera', '').replace(' ', '')
                if str1 in str2:
                    if self.comp_timestamps(cont[1].createdAt, cam[1].createdAt, self.TIMESTAMP_RANGE):
                        cameraEntries.remove(cam)
                        pairedEntries.append((cont, cam))

        return pairedEntries


    def merge_dualstreams(self, verbose=True, mailerror=False):
        if verbose:
            print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                  'Searching for DualStream entries')

        cats = load_statics_old(os.path.join(__basepath__, 'kaltura_categoryIds'))
        client = KalturaExtender()

        pairedEntries = client.get_dualstream_pairs()

        updateErrorCount = 0
        errorList = []
        for parent, child in pairedEntries:
            try:
                client.set_parent(parent=parent[1].id, child=child[1].id)
                client.update_entry(id=parent[1].id, updates={'categoriesIds': cats['Recordings']})
                print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                      'Updated:', end=' ')
                print('| p:', parent[0], parent[1].name, end=' ')
                print('| c:', child[0], child[1].name)
            except Exception as e:
                updateErrorCount += 1
                tb = traceback.format_exc()
                errEnd = '-' * 50 + '\n\n'
                errorList.append(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + " " + str(e) + '\n\n' + errEnd)
                errorList.append(tb)

        if errorList:
            print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                  'Encountered following errors')

            for e in errorList:
                print('-----')
                print(e)
            if mailerror:
                self.errorMailer.send_error_mail(__file__, errorList)

        if verbose:
            print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                  'Updated',
                  len(pairedEntries) - updateErrorCount,
                  'out of',
                  len(pairedEntries),
                  'entries')


def exportToCsv(list, path, specificVariables=None):
    if len(list) is 0:
        return

    if specificVariables is None:
        specificVariables = vars(list.values().__iter__().__next__()).keys()

    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=specificVariables)
        writer.writeheader()
        for x, o in sorted(list.items()):
            row = {}
            for p in vars(o).items():
                if p[0] not in specificVariables:
                    row[p[0]] = None
                    continue

                if p[1]:
                    row[p[0]] = kalturaObjectValueToString(p[0], p[1])
                else:
                    row[p[0]] = None

            writer.writerow(row)







