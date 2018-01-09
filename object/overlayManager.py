#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, sys, os, collections, itertools, re, string

from object.matcher import *
from object.reading import *
from object.readingGroup import *
from object.util import *

from utility.config import *

class OverlayManager:

    def __init__(s, config):
        s.config = config

        s.corrector01_json = None
        s.corrector05_json = None
        s.corrector01_files = {}
        s.corrector05_files = {}
        s.overlay_files = {}
        s.synopsis_files = {}

        s.corrector01Overlays = []
        s.corrector05Overlays = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        if web and hasattr(web, 'isWeb') and web.isWeb:
            web.debug(info)
        else:
            print(info) 

    def prepareAddresses(s, o_map):
        overlayLookup = {}
        for o_id, o_data in o_map.iteritems():
            is_corrector = False
            if o_id in s.corrector01Overlays or o_id in s.corrector05Overlays:
                is_corrector = True

            o_toks = re.split(r'\t', o_map[o_id])
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
                        tok = 'om.' if not is_corrector else ''
                    elif tok == 'om.' and is_corrector:
                        tok = 'OMIT'
                    addr_lookup[addr_idx] = tok.decode('utf-8')
                    addr_idx = addr_idx + 1
            o_verses[verse] = addr_lookup # last one
            overlayLookup[o_id] = o_verses

        return overlayLookup

    def processVUs(s, vmodel, o_lookup, o_type):
        for slot_idx, start_addr in enumerate(vmodel['addresses']):
            for vu in start_addr.variation_units:
                for o_id, o_verses in o_lookup.iteritems():
                    matcher = Matcher(vmodel, start_addr, slot_idx, vu, o_verses, o_id, o_type)
                    if o_type == Matcher.TYPE_CORRECTOR_01:
                        if vu.label == '5.27.5':
                            i = 23
                        matcher.addSinaiCorrector()
                    elif o_type == Matcher.TYPE_CORRECTOR_05:
                        matcher.addBezaeCorrector()

                    # for now, do not create new reading if no match
                    for reading in vu.readings:
                        if len(reading.manuscripts) == 0:
                            continue

                        is_match = False
                        if type(reading) is ReadingGroup:
                            for s_rdg in reading.readings:
                                is_match = matcher.isMatch(s_rdg, reading)
                                if is_match:
                                    break
                        else:
                            is_match = matcher.isMatch(reading, reading)

    def processCorrectorLayer(s, vmodel, layer, matcher_type):
        vu_map = {}
        for vu_json in layer:
            vu_map[vu_json['label']] = vu_json

        for slot_idx, start_addr in enumerate(vmodel['addresses']):
            for vu in start_addr.variation_units:
                if not vu_map.has_key(vu.label):
                    continue

                has_corrector = False
                vu_readings = []
                j_readings = []
                for rdg in vu_map[vu.label]['readings']:
                    if rdg['mss'].keys():
                        if rdg['correctors']:
                            has_corrector = True
                        j_readings.append(rdg)
                    else:
                        vu_reading = Reading(rdg['reading_text'])
                        for cor in rdg['correctors']:
                            if matcher_type == Matcher.TYPE_CORRECTOR_01:
                                vu_reading.sinai_correctors.append(cor)
                            elif matcher_type == Matcher.TYPE_CORRECTOR_05:
                                vu_reading.bezae_correctors.append(cor)
                        vu_readings.append(vu_reading)

                if has_corrector:
                    vu_mss = set()
                    j_mss = set()
                    r_pairs = itertools.product(vu.readings, j_readings)

                    matched_pairs = []
                    for pair in r_pairs:
                        if not pair[1]['correctors']:
                            continue

                        vu_mss = set(pair[0].manuscripts)
                        j_mss = set(pair[1]['mss'].keys())

                        if vu_mss and j_mss and vu_mss == j_mss:
                            matched_pairs.append(pair)

                    if not matched_pairs:
                        s.info('No reading match for', matcher_type, 'in', vu.label)
                        break

                    for pair in matched_pairs:
                        for corrector in pair[1]['correctors']:
                            if matcher_type == Matcher.TYPE_CORRECTOR_01:
                                pair[0].sinai_correctors.append(corrector)
                            elif matcher_type == Matcher.TYPE_CORRECTOR_05:
                                pair[0].bezae_correctors.append(corrector)

                for vu_reading in vu_readings:
                    vu.readings.append(vu_reading)

    def loadCorrectorJSON(s, vmodel, matcher_type):
        if matcher_type != Matcher.TYPE_CORRECTOR_01 and matcher_type != Matcher.TYPE_CORRECTOR_05:
            return False

        corrector_json = ''
        if not (matcher_type == Matcher.TYPE_CORRECTOR_01 and s.corrector01_json) and not (matcher_type == Matcher.TYPE_CORRECTOR_05 and s.corrector05_json):
            return False

        corrector_json = ''
        if matcher_type == Matcher.TYPE_CORRECTOR_01:
            corrector_json = s.config.get('outputFolder') + '/' + s.corrector01_json + '.json'
        elif matcher_type == Matcher.TYPE_CORRECTOR_05:
            corrector_json = s.config.get('outputFolder') + '/' + s.corrector05_json + '.json'

        if not corrector_json or not os.path.isfile(corrector_json):
            return False

        file = open(corrector_json, 'r')
        jsondata = file.read().decode('utf-8')
        file.close()

        correctorLayer = json.loads(jsondata)
        s.processCorrectorLayer(vmodel, correctorLayer, matcher_type)

        return True

    def loadOverlayType(s, vmodel, files_map, matcher_type, is_manuscript):
        if s.loadCorrectorJSON(vmodel, matcher_type):
            return

        overlay_map = {}
        for o_id, o_file in files_map.iteritems():
            if os.path.isfile(o_file):
                file = open(o_file, 'r')
                o_data = file.read().decode('utf-8-sig') # Remove BOM
                o_data = o_data.encode('utf-8') # Reencode without BOM
                overlay_map[o_id] = o_data
                file.close()
            if is_manuscript:
                vmodel['manuscripts'].append(o_id)

        o_lookup = s.prepareAddresses(overlay_map)
        s.processVUs(vmodel, o_lookup, matcher_type)

    def loadOverlays(s, vmodel):
        s.loadOverlayType(vmodel, s.overlay_files, Matcher.TYPE_CONTINUOUS, True)
        s.loadOverlayType(vmodel, s.synopsis_files, Matcher.TYPE_SYNOPTIC, False)
        s.loadOverlayType(vmodel, s.corrector01_files, Matcher.TYPE_CORRECTOR_01, False)
        s.loadOverlayType(vmodel, s.corrector05_files, Matcher.TYPE_CORRECTOR_05, False)

    def loadFiles(s, dir):
        c = s.config
        s.info('loading overlays from', dir)

        overlays = c.get('msOverlays')
        synopses = c.get('synopticOverlays')

        # Corrector JSON preferred, correctors matched to all readings!
        s.corrector01_json = c.get('corrector01JSON')
        s.corrector05_json = c.get('corrector05JSON')
        s.corrector01Overlays = c.get('corrector01Overlays')
        s.corrector05Overlays = c.get('corrector05Overlays')

        s.overlay_files = {}
        for o_id in overlays:
            o_file = s.config.get('variantFolder') + dir + '/' + o_id + '.txt'
            s.overlay_files[o_id] = o_file

        s.synopsis_files = {}
        for s_id in synopses:
            s_file = s.config.get('variantFolder') + dir + '/' + s_id + '.txt'
            s.synopsis_files[s_id] = s_file

        s.corrector01_files = {}
        for c_id in s.corrector01Overlays:
            c_file = s.config.get('variantFolder') + dir + '/' + c_id + '.txt'
            s.corrector01_files[c_id] = c_file

        s.corrector05_files = {}
        for c_id in s.corrector05Overlays:
            c_file = s.config.get('variantFolder') + dir + '/' + c_id + '.txt'
            s.corrector05_files[c_id] = c_file
