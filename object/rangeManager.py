#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, sys, os, string, re, json

from object.jsonDecoder import *
from object.jsonEncoder import *
from object.util import *

from utility.config import *

class RangeManager:

    def __init__(s):
        s.config = None
        s.chapterLookup = {}

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

    def processOverlays(s, vmodel, overlay_data):
        chapter = vmodel['chapter']
        o_lookup = {}
        for o_id, o_data in overlay_data.iteritems():
            o_toks = re.split(r'\t', overlay_data[o_id])
            o_verses = {}
            addr_lookup = {}
            verse = 0
            addr_idx = 0
            for tok in o_toks:
                if tok.isdigit():
                    if addr_lookup:
                        o_verses[verse] = addr_lookup
                    verse = int(tok)
                    addr_idx = 1
                    addr_lookup = {}
                else:
                    tok = re.sub('[\[\]]', '', tok)
                    if not tok:
                        tok = 'om.'
                    addr_lookup[addr_idx] = tok.decode('utf-8')
                    addr_idx = addr_idx + 1
            o_verses[verse] = addr_lookup # last one
            o_lookup[o_id] = o_verses

        for slot_idx, start_addr in enumerate(vmodel['addresses']):
            for vu in start_addr.variation_units:
                for o_id, o_verses in o_lookup.iteritems():
                    has_match = False
                    for reading in vu.readings:
                        if len(reading.manuscripts) == 0:
                            continue

                        if vu.label == '14.70.25,39':
                            i = 0
                            j = 1
                            k = i + j

                        is_match = False
                        if type(reading) is ReadingGroup:
                            for s_rdg in reading.readings:
                                is_match = s.isOverlayMatch(s_rdg, vmodel, start_addr, slot_idx, o_verses)
                                if is_match:
                                    break
                        else:
                            is_match = s.isOverlayMatch(reading, vmodel, start_addr, slot_idx, o_verses)

                        if is_match:
                            reading.manuscripts.append(o_id)
                            has_match = True
                            break

                    # for now, do not create new reading if has_match == False

    def isOverlayMatch(s, reading, vmodel, start_addr, slot_idx, o_verses):
        is_match = True
        is_deferable = False
        deferred_text = None
        o_reading = ''
        for ru in reading.readingUnits:
            ru_addr = start_addr
            for idx in range(slot_idx + 1, len(vmodel['addresses'])):
                if ru.verse_num == ru_addr.verse_num and ru.addr_idx == ru_addr.addr_idx:
                    break;

                ru_addr = vmodel['addresses'][idx]

            try:
                o_text = o_verses[ru.verse_num][ru.addr_idx]
                if len(o_reading) > 0 and o_text == '-':
                    o_text = 'om.' # handle long sparse matches where final '-' is interpreted as 'om.' by non-overlay MSS, see 14.70.25,39 where na28 == 03

                text = ru.text
                if text != 'om.':
                    deferred_text = None
                if deferred_text:
                    text = deferred_text
                alt_forms = ru_addr.getAltFormsForReadingUnit(text)

                if not o_text in alt_forms:
                    is_match = False # unless intervening overlay addrs == 'om.' and next overlay addr is match
                    is_deferable = False
                    if o_text == 'om.':
                        is_deferable = True
                        if not deferred_text: # not already deferring!
                            deferred_text = ru.text
                    else: # overlay non-empty, start over
                        deferred_text = None
                    if not is_match and not is_deferable:
                        break
                else: # overlay match, start over
                    is_match = True # reachable only when still matching
                    deferred_text = None
                    if o_text == 'om.' or o_text == '-':
                        continue
                    if len(o_reading) > 0:
                        o_reading = o_reading + ' '
                    o_reading = o_reading + o_text
            except KeyError as e:
                is_match = False
                print 'Key Error: ' + str(e) + ', chapter=' + ru_addr.chapter_num + ', verse=' + str(ru.verse_num) + ', address=' + str(ru.addr_idx)
        return is_match

    def loadVariants(s, varfile, overlay_files):
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
        overlay_data = {}
        for o_id, o_file in overlay_files.iteritems():
            if os.path.isfile(o_file):
                with open(o_file, 'r') as file:
                    o_data = file.read().decode('utf-8-sig') # Remove BOM
                    o_data = o_data.encode('utf-8') # Reencode without BOM
                    overlay_data[o_id] = o_data
                    file.close()
            vmodel['manuscripts'].append(o_id)

        s.processOverlays(vmodel, overlay_data)

        chapter = vmodel['chapter']
        if s.chapterLookup.has_key(chapter):
            lookup = s.chapterLookup[chapter]
            vmodel = s.appendModel(lookup, vmodel)
        s.chapterLookup[chapter] = vmodel

    def load(s):
        c = s.config = Config('processor-config.json')
        s.info('Loading variant data')

        vcachefile = c.get('variantDataCache')
        if os.path.isfile(vcachefile):
            with open(vcachefile, 'r') as file:
                j_data = file.read().decode('utf-8-sig') # Remove BOM
                j_data = j_data.encode('utf-8') # Reencode without BOM
                file.close()
            s.chapterLookup = json.loads(j_data, cls=ComplexDecoder)
        else:
            vardata = c.get('variantData')
            overlays = c.get('msOverlays')
            for obj in vardata:
                varfile = s.config.get('variantFolder') + obj['subdir'] + '/' + obj['file'] + '.json'

                overlay_files = {}
                for o_id in overlays:
                    o_file = s.config.get('variantFolder') + obj['subdir'] + '/' + o_id + '.txt'
                    overlay_files[o_id] = o_file

                s.info('loading', varfile)
                s.loadVariants(varfile, overlay_files)
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

            # Is this used?
            #rcachefile = c.get('variantFolder') + '/_cache/' + range_id + '.json'
            #jdata = json.dumps(variantModel, cls=ComplexEncoder, ensure_ascii=False)
            #with open(rcachefile, 'w+') as file:
            #    file.write(jdata.encode('UTF-8'))
            #    file.close()

        return variantModel
