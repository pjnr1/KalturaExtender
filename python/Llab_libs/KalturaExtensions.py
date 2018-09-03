import re
import os
import datetime
from Llab_libs import FuncDecorators

__basepath__ = os.path.dirname(os.path.realpath(__file__))

# Kaltura imports
from Kaltura.KalturaClient import *
from Kaltura.KalturaClient.Base import *
from Kaltura.KalturaClient.Plugins.Core import *


def printKalturaObject(object, specificVariables=None, counter=None, levelOfIndent=0):
    indent = '\t' * levelOfIndent

    def printOut(a, values):
        if 'Kaltura' in type(values).__name__:
            print('{:s}{:s}:\n{:s}\t{:s}'.format(indent, a, indent, values.getValue().__str__()))
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


class KalturaExtender:
    TIMESTAMP_RANGE = 30

    client = NotImplemented
    ks = NotImplemented

    def __init__(self):
        s = self.load_kaltura_client_statics()
        # Initial API client setup
        cfg = KalturaConfiguration(s['partnerId'])
        cfg.serviceUrl = s['serviceUrl']
        self.client = KalturaClient(cfg)
        self.ks = self.client.session.start(s['adminSecret'], s['userId'], KalturaSessionType.ADMIN, s['partnerId'])
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
            pIds = load_kaltura_statics("kaltura_thumbParamsIds")
            paramId = pIds['default']
        elif type(paramId) is type(str):
            pIds = load_kaltura_statics("kaltura_thumbParamsIds")
            paramId = pIds[paramId]

        try:
            res = self.client.thumbAsset.generateByEntryId(entryId=id,
                                                           destThumbParamsId=paramId)
            self.client.thumbAsset.setAsDefault(res.id)
        except:
            print('error', id)


    def get_kaltura_client(self):
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

    def getDualStreamEntries(self, printResult=True):
        mediaFilter = KalturaMediaEntryFilter(mediaTypeEqual=1, tagsLike='DualStream-child')
        res = self.get_kaltura_client().media.list(mediaFilter)
    
        i = 0
        output = {}
        for media in res.objects:
            output[media.id] = media
    
            if printResult:
                printKalturaObject(media, counter=i)
    
            i += 1
    
        return output
    
    def getDualStreamStreams(self, printResult=True):
        mediaFilter = KalturaMediaEntryFilter(mediaTypeEqual=201, tagsLike='dualstream')
        res = self.get_kaltura_client().media.list(mediaFilter)
        
        i = 0
        output = {}
        for media in res.objects:
            output[media.id] = media
            
            if printResult:
                printKalturaObject(media, counter=i)
            
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


def mergeDualStreamPairs(verbose=True):
    if verbose:
        print(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
              'Searching for DualStream entries')

    cats = load_kaltura_statics(os.path.join(__basepath__, 'kaltura_categoryIds'))
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
        except Exception as e:
            updateErrorCount += 1
            errorList.append(e)

    if verbose:
        print(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
              'Updated',
              len(pairedEntries)-updateErrorCount,
              'out of',
              len(pairedEntries),
              'entries')

