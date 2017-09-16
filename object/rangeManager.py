#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, string, re, json

from object.jsonDecoder import *
from object.jsonEncoder import *
from object.util import *

from utility.config import *

class RangeManager:

    def __init__(s):
        s.chapterLookup = {}

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
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

        chapter = vmodel['chapter']
        if s.chapterLookup.has_key(chapter):
            lookup = s.chapterLookup[chapter]
            vmodel = s.appendModel(lookup, vmodel)
        s.chapterLookup[chapter] = vmodel

    def load(s):
        c = s.config = Config('processor-config.json')
        s.info('loading variant data')

        vcachefile = c.get('variantDataCache')
        if os.path.isfile(vcachefile):
            with open(vcachefile, 'r') as file:
                j_data = file.read().decode('utf-8-sig') # Remove BOM
                j_data = j_data.encode('utf-8') # Reencode without BOM
                file.close()
            s.chapterLookup = json.loads(j_data, cls=ComplexDecoder)
        else:
            vardata = c.get('variantData')
            for obj in vardata:
                varfile = s.config.get('variantFolder') + obj['subdir'] + '/' + obj['file'] + '.json'

                s.info('loading', varfile)
                s.loadVariants(varfile)
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

        variantModel = { 'addresses': [], 'manuscripts': [] }
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

                variantModel['manuscripts'] = sorted(list(set(variantModel['manuscripts']).union(set(c_data['manuscripts']))), cmp=sortMSS)

            rcachefile = c.get('variantFolder') + '/_cache/' + range_id + '.json'
            jdata = json.dumps(variantModel, cls=ComplexEncoder, ensure_ascii=False)
            with open(rcachefile, 'w+') as file:
                file.write(jdata.encode('UTF-8'))
                file.close()

        return variantModel
