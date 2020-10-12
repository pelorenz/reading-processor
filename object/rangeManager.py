#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, sys, os, string, re, json

from object.jsonDecoder import *
from object.jsonEncoder import *
from object.overlayManager import *
from object.util import *
from object.wordCounter import *

from utility.config import *

class RangeManager:

    def __init__(s):
        s.config = None
        s.chapterLookup = {}
        s.overlayManager = None
        s.word_map_03 = {}
        s.word_map_05 = {}

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        if web and hasattr(web, 'isWeb') and web.isWeb:
            web.debug(info)
        else:
            print(info) 

    def appendModel(s, base, nmod):
        base['addresses'].extend(nmod['addresses'])
        base['manuscripts'] = sorted(list(set(base['manuscripts']).union(set(nmod['manuscripts']))), cmp=sortMSS)
        return base

    def loadVariants(s, varfile):
        j_data = ''
        with open(varfile, 'r') as file:
            j_data = file.read().decode('utf-8-sig') # Remove BOM
            j_data = j_data.encode('utf-8') # Reencode without BOM
            file.close()

        # Load JSON
        vmodel = json.loads(j_data, cls=ComplexDecoder)

        # normalize filename, e.g. 'mark-06'
        vmodel['filename'] = re.search(r'^(mark\-\d{2,2})', vmodel['_filename']).group(1)

        # process overlays
        s.overlayManager.loadOverlays(vmodel)

        # concat and assign models
        chapter = vmodel['chapter']
        if s.chapterLookup.has_key(chapter):
            lookup = s.chapterLookup[chapter]
            vmodel = s.appendModel(lookup, vmodel)
        s.chapterLookup[chapter] = vmodel

    def loadWordMaps(s):
        c = s.config

        cache_03 = c.get('variantDataCacheDir') + 'words-03-cache.json'
        if os.path.isfile(cache_03):
            file = open(cache_03, 'r')
            j_data = file.read().decode('utf-8-sig') # Remove BOM
            j_data = j_data.encode('utf-8') # Reencode without BOM
            s.word_map_03 = json.loads(j_data)
            file.close()

        cache_05 = c.get('variantDataCacheDir') + 'words-05-cache.json'
        if os.path.isfile(cache_05):
            file = open(cache_05, 'r')
            j_data = file.read().decode('utf-8-sig') # Remove BOM
            j_data = j_data.encode('utf-8') # Reencode without BOM
            s.word_map_05 = json.loads(j_data)
            file.close()

    def load(s, is_refresh):
        c = s.config = Config('processor-config.json')
        s.info('Loading variant data')

        vcachefile = c.get('variantDataCache')
        if os.path.isfile(vcachefile) and not is_refresh:
            with open(vcachefile, 'r') as file:
                j_data = file.read().decode('utf-8-sig') # Remove BOM
                j_data = j_data.encode('utf-8') # Reencode without BOM
                file.close()
            s.chapterLookup = json.loads(j_data, cls=ComplexDecoder)
            s.loadWordMaps()
        else:
            s.overlayManager = OverlayManager(c)

            vardata = c.get('variantData')
            for obj in vardata:
                varfile = s.config.get('variantFolder') + obj['subdir'] + '/' + obj['file'] + '.json'

                s.overlayManager.loadFiles(obj['subdir'])

                s.info('loading', varfile)
                s.loadVariants(varfile)

            wc = WordCounter(c)
            wc.computeIndexes(s.chapterLookup)
            s.word_map_03 = wc.word_map_03
            s.word_map_05 = wc.word_map_05

            s.save()

    def save(s):
        c = s.config = Config('processor-config.json')
        s.info('Saving variant data')

        vcachefile = c.get('variantDataCache')
        jdata = json.dumps(s.chapterLookup, cls=ComplexEncoder, ensure_ascii=False)
        with open(vcachefile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

    def getModel(s, range_id):
        c = s.config = Config('processor-config.json')
        s.info('Retrieving variant model')

        variantModel = { 'addresses': [], 'manuscripts': [], 'address_lookup': {} }
        range_data = c.get('rangeData')
        if range_data.has_key(range_id):
            ranges = range_data[range_id]
            for r in ranges:
                c_num = r['chapter']
                s_verse = r['startVerse']
                e_verse = r['endVerse']

                c_data = s.chapterLookup[c_num]

                v_list = []
                for vidx in range(s_verse, e_verse + 1):
                    v_list.append(vidx)

                v_set = set(v_list)
                for addr in c_data['addresses']:
                    if addr.verse_num in v_set:
                        variantModel['addresses'].append(addr)

                        key = addr.chapter_num + '-' + str(addr.verse_num)
                        verse_addrs = []
                        if variantModel['address_lookup'].has_key(key):
                            verse_addrs = variantModel['address_lookup'][key]
                        else:
                            variantModel['address_lookup'][key] = verse_addrs
                        verse_addrs.append(addr)

                variantModel['manuscripts'] = sorted(list(set(variantModel['manuscripts']).union(set(c_data['manuscripts']))), cmp=sortMSS)

        return variantModel
