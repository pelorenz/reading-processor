#! python2.7
# -*- coding: utf-8 -*-

import sys, os, argparse, urllib, subprocess, string, re, shutil, datetime, operator, json

from utility.config import *
from utility.options import *

from object.address import *
from object.jsonDecoder import *
from object.jsonEncoder import *
from object.jsonProcessor import *
from object.manuscript import *
from object.textForm import *
from object.textInstance import *
from object.verseDelimiter import *


class Processor:

    def __init__(s):
        # all addresses
        s.addresses = []
        s.mss = []

    def info(s, *args):
        info = ''
        if s.options.verbose:
            for i, arg in enumerate(args):
                if i > 0: info += ' '
                info += str(arg).strip()
            print info

    def readMorphCache(s):
        c = s.config

        morphdata = ''
        cachefile = c.get('cacheFolder') + c.get('morphCache')
        with open(cachefile, 'r') as file:
            morphdata = file.read().decode('utf-8')
            file.close()
        TextForm.morph_cache = json.loads(morphdata, cls=ComplexDecoder)

    def writeMorphCache(s):
        c = s.config

        morphcache = json.dumps(TextForm.morph_cache, cls=ComplexEncoder, ensure_ascii=False)
        cachefile = c.get('cacheFolder') + c.get('morphCache')
        with open(cachefile, 'w+') as file:
            file.write(morphcache.encode('UTF-8'))
            file.close()

    def processCSV(s, filename, language):
        c = s.config
        o = s.options
        s.info('processing', filename)

        # load data
        csvdata = ''
        csvfile = c.get('inputFolder') + str(filename)
        with open(csvfile, 'r') as file:
            s.info('reading', filename)
            csvdata = file.read().decode('utf-8')
            file.close()

        raw_witnesses = csvdata.split(u'\n')

        line_idx = 0
        for line in raw_witnesses:
            if not line:
                continue

            isNewMs = True
            tok_idx = 0
            addr_idx = 1
            ms_id = None
            cur_ms = None
            cur_slot = None
            cur_verse = None
            raw_tokens = line.split(u'\t')
            for raw_tok in raw_tokens:
                raw_tok = raw_tok.strip()
                # IMPORTANT - uncomment for Mark 1!
                # remove text between parentheses
                #raw_tok = re.sub("[\(].*?[\)]", "", raw_tok)

                # remove text between square brackets
                #raw_tok = re.sub("[\[].*?[\]]", "", raw_tok)

                # remove text between angle brackets
                #raw_tok = re.sub("[\<].*?[\>]", "", raw_tok)

                # remove other specified characters
                for char in c.get('ignoreChars'):
                    raw_tok = raw_tok.replace(char, '')
                for char in c.get('ignoreUnicode'):
                    raw_tok = raw_tok.replace(char, '')

                # manuscript identifier comes first
                if isNewMs:
                    ms_id = raw_tok
                    cur_ms = Manuscript(ms_id, language)
                    s.mss.append(cur_ms)
                    s.info('processing manuscript', ms_id)
                    isNewMs = False
                    continue

                # Either verse reference or address
                verse_num = None
                if raw_tok.isdigit():
                    # verse
                    verse_num = cur_verse = raw_tok
                    addr_idx = 1

                # first pass, initialize data structures
                if line_idx == 0:
                    if verse_num:
                        cur_slot = VerseDelimiter(tok_idx, cur_verse)
                    else:
                        cur_slot = Address(tok_idx, cur_verse, addr_idx)

                    s.addresses.append(cur_slot)
                else:
                    cur_slot = s.addresses[tok_idx]

                # process content for address
                if isinstance(cur_slot, Address):
                    txt_inst = TextInstance(tok_idx, cur_slot.verse_num, cur_slot.addr_idx, cur_ms, raw_tok)
                    cur_slot.text_instances.append(txt_inst)
                    addr_idx = addr_idx + 1

                tok_idx = tok_idx + 1

            line_idx = line_idx + 1

    def processAddresses(s, language):
        for addr in s.addresses:
            if isinstance(addr, Address):
                s.info('processing verse', addr.verse_num, ', address', str(addr.addr_idx), 'with', str(len(addr.text_instances)), 'instances')
                addr.initializeTextForms(language)

    def saveJSON(s, filename):
        c = s.config
        o = s.options

        parts = filename.split('.')
        if len(parts) <> 2:
            return

        language = 'greek'
        if parts[0].find('lat') > -1:
            language = 'latin'

        data = json.dumps({ '_type': 'base', '_language': language, '_filename': parts[0], 'manuscripts': s.mss, 'addresses': s.addresses, 'maxFormsAtAddress': Address.max_forms, 'maxNonSingularFormsAtAddress': Address.max_non_sing }, cls=ComplexEncoder, ensure_ascii=False) #, indent=2, sort_keys=True)

        outputfile = c.get('outputFolder') + parts[0] + '.json'
        with open(outputfile, 'w+') as file:
            file.write(data.encode('utf-8'))
            file.close()

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        if o.file:
            files = [o.file + '.csv', o.file + '-lat.csv']
        else:
            files = c.get('csvFiles')

        # Load morph cache
        s.readMorphCache()

        try:
            if (files):
                for filename in files:
                    parts = filename.split('.')
                    if len(parts) <> 2:
                        return

                    language = 'greek'
                    if parts[0].find('lat') > -1:
                        language = 'latin'

                    s.addresses = []
                    s.mss = []
                    Address.max_forms = 0
                    Address.max_non_sing = 0
                    s.processCSV(filename, language)
                    s.processAddresses(language)
                    s.saveJSON(filename)
        finally:
            # Save morph cache
            s.writeMorphCache()

        # render html
        jsonProcessor = JSONProcessor()
        jsonProcessor.options = s.options
        jsonProcessor.config = s.config

        if o.file:
            files = [o.file + '.json', o.file + '-lat.json']
        else:
            files = c.get('jsonFiles')

        if (files):
            for filename in files:
                jsonProcessor.processJSON(filename)
            jsonProcessor.render(files[0])

# Invoke via entry point
# csvProcessor.py -v -f [filename minus suffix]
Processor().main(sys.argv[1:])
