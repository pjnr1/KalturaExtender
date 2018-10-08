import csv
import re
import os
import traceback
from datetime import datetime
from Llab_libs import FuncDecorators
from Llab_libs.statics_helper import load_statics
from Llab_libs.mail_helper import LLabMailHelper

__basepath__ = os.path.dirname(os.path.realpath(__file__))
listOfUnixTimeStampVariables = ['createdAt', 'updatedAt', 'lastLoginTime',
                                'statusUpdatedAt', 'deletedAt', 'mediaDate',
                                'firstBroadcast', 'lastBroadcast']

# Kaltura imports
from Kaltura.KalturaClient import *
from Kaltura.KalturaClient.Base import *
from Kaltura.KalturaClient.Plugins.Core import *


def printKalturaObject(object, specificVariables=None, counter=None, levelOfIndent=0):
    indent = '\t' * levelOfIndent

    def printOut(a, values):
        if 'Kaltura' in type(values).__name__:
            print('{:s}{:s}:\n{:s}\t{:s}'.format(indent, a, indent, values.getValue().__str__()))
        elif any(x in a for x in listOfUnixTimeStampVariables):
            dt = datetime.fromtimestamp(values).strftime("%Y-%m-%d %H:%M:%S")
            print('{:s}{:s}:\n{:s}\t{:s}'.format(indent, a, indent, dt))
        else:
            print('{:s}{:s}:\n{:s}\t{:s}'.format(indent, a, indent, values.__str__()))

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


errorMailer = LLabMailHelper()


class KalturaExtender:
    TIMESTAMP_RANGE = 30

    client = NotImplemented
    ks = NotImplemented
    categoryIds = NotImplemented

    def __init__(self, log=False):
        s = load_statics(os.path.join(__basepath__, 'kaltura_statics.secret'))
        self.categoryIds = load_statics(os.path.join(__basepath__, 'kaltura_categoryIds'))
        # Initial API client setup
        cfg = KalturaConfiguration(s['partnerId'])
        cfg.serviceUrl = s['serviceUrl']
        self.client = KalturaClient(cfg)
        # Start session
        self.ks = self.client.session.start(s['adminSecret'], None, KalturaSessionType.ADMIN, s['partnerId'])
        self.client.setKs(self.ks)

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
    def apply_filter(mediaFilter, filters):
        if filters is not None:
            for f in filters:
                if hasattr(mediaFilter, f):
                    setattr(mediaFilter, f, filters[f])
                else:
                    print('Warning:', filters[f], 'is not a valid KalturaMediaEntryFilter() attribute')

    @staticmethod
    def compareTimeStamps(t1, t2, r=0):
        t0 = t1 - t2
        t0 = abs(t0)
        return not t0 > r

    def generateThumbAndSetAsDefault(self, id, paramId=None):
        if not paramId:
            pIds = load_statics("kaltura_thumbParamsIds")
            paramId = pIds['default']
        elif type(paramId) is type(str):
            pIds = load_statics("kaltura_thumbParamsIds")
            paramId = pIds[paramId]

        try:
            res = self.client.thumbAsset.generateByEntryId(entryId=id,
                                                           destThumbParamsId=paramId)
            self.client.thumbAsset.setAsDefault(res.id)
        except:
            print('error', id)

    def getClient(self):
        if self.client is NotImplemented:
            raise RuntimeError('KalturaExtender::client not loaded!')
        return self.client

    def getEntries(self, filters=None, entryType='media', printResult=False, specificVariables=None):
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

    def getExistingLiveEntries(self, printResult=True, specificVariables=None):
        f = KalturaLiveEntryFilter()
        res = self.get_kaltura_client().liveStream.list(f)

        i = 0
        output = {}
        for stream in res.objects:
            output[stream.id] = stream

            if printResult:
                printKalturaObject(stream, counter=i, specificVariables=specificVariables)

            i += 1

        return output

    def getExistingUsers(self, printResult=True, onlyAdmins=False, specificVariables=None):
        f = KalturaUserFilter()
        p = KalturaFilterPager()
        p.pageSize = 500
        res = self.get_kaltura_client().user.list(f, p)
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

    def getUsersEntries(self, username, filters=None, printResult=False, specificVariables=None):
        mediaFilter = KalturaMediaEntryFilter()
        mediaFilter.userIdEqual = username
        self.apply_filter(mediaFilter, filters)

        res = self.get_kaltura_client().media.list(mediaFilter)

        i = 0
        output = {}
        for media in res.objects:
            output[media.id] = media

            if printResult:
                printKalturaObject(media, specificVariables=specificVariables, counter=i)

            i += 1

        return output

    def setParentEntryId(self, parent, child, entryType='media'):
        modifierEntry = KalturaMediaEntry()
        modifierEntry.parentEntryId = parent

        return getattr(self.client, entryType).update(child, modifierEntry)

    def updateEntry(self, id, updates, entryType='media', modifierEntry=KalturaMediaEntry()):
        if updates is not None:
            for u in updates:
                if hasattr(modifierEntry, u):
                    setattr(modifierEntry, u, updates[u])

        return getattr(self.client, entryType).update(id, modifierEntry)

    def deleteEntry(self, id, entryType):
        return getattr(self.client, entryType).delete(id)


    def getDualStreamChannels(self):
        cats = load_statics(os.path.join(__basepath__, 'kaltura_categoryIds'))

        return self.getEntries(filters={'categoriesIdsMatchAnd': self.categoryIds['Streams'],
                                        'mediaTypeEqual': 201},
                               entryType='liveStream')

    def getDualStreamEntryPairs(self):
        streamEntries = self.getDualStreamChannels()

        readyEntries = {}
        for streams in streamEntries.items():
            listOfEntries = self.getEntries(filters={'rootEntryIdEqual': streams[0],
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
                    if self.compareTimeStamps(cont[1].createdAt, cam[1].createdAt, self.TIMESTAMP_RANGE):
                        cameraEntries.remove(cam)
                        pairedEntries.append((cont, cam))

        return pairedEntries


def exportToCsv(list, path, specificVariables=None):
    if specificVariables is None:
        return None

    def getStr(value):
        if 'Kaltura' in type(value).__name__:
            return value.getValue().__str__()
        else:
            return value.__str__()

    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=specificVariables)
        writer.writeheader()
        for x, object in list.items():
            row = {}
            for p in vars(object).items():
                if p[0] in specificVariables:
                    row[p[0]] = getStr(p[1])

            writer.writerow(row)


def mergeDualStreamPairs(verbose=True):
    if verbose:
        print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
              'Searching for DualStream entries')

    cats = load_statics(os.path.join(__basepath__, 'kaltura_categoryIds'))
    client = KalturaExtender()

    streamEntries = client.getEntries(filters={'categoriesIdsMatchAnd': cats['Streams'],
                                               'mediaTypeEqual': 201},
                                      entryType='liveStream')

    readyEntries = {}
    for streams in streamEntries.items():
        listOfEntries = client.getEntries(filters={'rootEntryIdEqual': streams[0],
                                                   'categoriesIdsNotContains': cats['Recordings'],
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
                if client.compareTimeStamps(cont[1].createdAt, cam[1].createdAt, client.TIMESTAMP_RANGE):
                    pairedEntries.append((cont, cam))
                    cameraEntries.remove(cam)

    updateErrorCount = 0
    errorList = []
    for parent, child in pairedEntries:
        try:
            client.setParentEntryId(parent=parent[1].id, child=child[1].id)
            client.updateEntry(id=parent[1].id, updates={'categoriesIds': cats['Recordings']})
            print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                  'Updated:', end=' ')
            print('parent:', parent[0], parent[1].name, end='')
            print('child:', child[0], child[1].name)
        except Exception as e:
            updateErrorCount += 1
            tb = traceback.format_exc()
            errorList.append(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + " " + str(e))
            errorList.append(tb)

    if errorList:
        print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
              'Encountered following errors')

        for e in errorList:
            print('-----')
            print(e)

        errorMailer.send_error_mail(__file__, errorList)

    if verbose or len(pairedEntries):
        print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
              'Updated',
              len(pairedEntries)-updateErrorCount,
              'out of',
              len(pairedEntries),
              'entries')


def generateThumbForAll(verbose=True):
    raise NotImplementedError

    if verbose:
        print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
              'Searching for entries without thumbs')

    cats = load_statics(os.path.join(__basepath__, 'kaltura_categoryIds'))
    client = KalturaExtender()

    streamEntries = client.getEntries(filters={'categoriesIdsMatchAnd': cats['Streams'],
                                               'mediaTypeEqual': 201},
                                      entryType='liveStream')

    readyEntries = {}
    for streams in streamEntries.items():
        listOfEntries = client.getEntries(filters={'rootEntryIdEqual': streams[0],
                                                   'mediaTypeEqual': 1,
                                                   'statusEqual': KalturaEntryStatus.READY})

        for entry in listOfEntries.items():
            readyEntries[entry[0]] = entry[1]

    if verbose:
        for entries in readyEntries.items():
            print(entries[0], entries[1].id)
            thumbs = client.get_kaltura_client().thumbAsset.getByEntryId(entries[1].id)
            for thumb in thumbs:
                print(thumb.size)
                print(datetime.fromtimestamp(thumb.createdAt).strftime("%Y-%m-%d %H:%M:%S"))

        print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
              'Found',
              len(readyEntries),
              'entries without thumbnails.')

    return  # OBS OBS OBS RETURNS HERE !!!

    errorList = []
    for entries in readyEntries.items():
        try:
            client.generateThumbAndSetAsDefault(id=entries, paramId=324)
        except Exception as e:
            errorList.append(e)

    if errorList:
        print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'Encountered following errors')

        for i, e in enumerate(errorList):
            print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), i, e)

    if verbose:
        print(str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
              'Encountered following errors')
