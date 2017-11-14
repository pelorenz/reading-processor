#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, sys, os, string, re

from object.matcher import *
from object.reading import *
from object.readingGroup import *
from object.util import *

from utility.config import *

class OverlayManager:

    def __init__(s, config):
        s.config = config

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        if web and hasattr(web, 'isWeb') and web.isWeb:
            web.debug(info)
        else:
            print(info) 

    def prepareOverlays(s, o_map):
        overlayLookup = {}
        for o_id, o_data in o_map.iteritems():
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
                        tok = 'om.'
                    addr_lookup[addr_idx] = tok.decode('utf-8')
                    addr_idx = addr_idx + 1
            o_verses[verse] = addr_lookup # last one
            overlayLookup[o_id] = o_verses

        return overlayLookup

    def processOverlays(s, vmodel, o_lookup, o_type):
        chapter = vmodel['chapter']
        for slot_idx, start_addr in enumerate(vmodel['addresses']):
            for vu in start_addr.variation_units:
                for o_id, o_verses in o_lookup.iteritems():
                    # for now, do not create new reading if no match
                    for reading in vu.readings:
                        if len(reading.manuscripts) == 0:
                            continue

                        is_match = False
                        matcher = Matcher(vmodel, start_addr, slot_idx, vu, o_verses, o_id, o_type)
                        if type(reading) is ReadingGroup:
                            for s_rdg in reading.readings:
                                is_match = matcher.isMatch(s_rdg, reading)
                                if is_match:
                                    break
                        else:
                            is_match = matcher.isMatch(reading, reading)

    def loadOverlays(s, vmodel):
        # process witness overlays
        continuous_map = {}
        for o_id, o_file in s.overlay_files.iteritems():
            if os.path.isfile(o_file):
                with open(o_file, 'r') as file:
                    o_data = file.read().decode('utf-8-sig') # Remove BOM
                    o_data = o_data.encode('utf-8') # Reencode without BOM
                    continuous_map[o_id] = o_data
                    file.close()
            vmodel['manuscripts'].append(o_id)

        o_lookup = s.prepareOverlays(continuous_map)
        s.processOverlays(vmodel, o_lookup, Matcher.TYPE_CONTINUOUS)

        # process synoptic overlays
        synopsis_map = {}
        for o_id, o_file in s.synopsis_files.iteritems():
            if os.path.isfile(o_file):
                with open(o_file, 'r') as file:
                    o_data = file.read().decode('utf-8-sig') # Remove BOM
                    o_data = o_data.encode('utf-8') # Reencode without BOM
                    synopsis_map[o_id] = o_data
                    file.close()
            # don't append synoptic ||'s to MSS

        o_lookup = s.prepareOverlays(synopsis_map)
        s.processOverlays(vmodel, o_lookup, Matcher.TYPE_SYNOPTIC)

    def loadFiles(s, dir):
        c = s.config
        s.info('loading overlays from', dir)

        overlays = c.get('msOverlays')
        synopses = c.get('synopticOverlays')

        s.overlay_files = {}
        for o_id in overlays:
            o_file = s.config.get('variantFolder') + dir + '/' + o_id + '.txt'
            s.overlay_files[o_id] = o_file

        s.synopsis_files = {}
        for s_id in synopses:
            s_file = s.config.get('variantFolder') + dir + '/' + s_id + '.txt'
            s.synopsis_files[s_id] = s_file
