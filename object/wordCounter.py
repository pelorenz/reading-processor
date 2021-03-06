#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, string, itertools, copy, json

from object.util import *

from utility.config import *

class WordCounter:

    def __init__(s, config):
        s.config = config
        s.wordIndex03 = 0
        s.wordIndex05 = 0

        s.word_map_03 = {}
        s.word_map_05 = {}

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info) 

    def computeIndexes(s, chapterLookup):
        c = s.config = Config('processor-config.json')
        s.info('Computing word indexes')

        lastTextIndex03 = 0
        lastTextIndex05 = 0
        vu_stack_03 = []
        vu_stack_05 = []

        file = open(c.get('outputFolder') + 'word-counter.log', 'w+')
        file.write('03 Index\t03 Verse\t05 Index\t05 Verse\n')
        for i in range(1, 17):
            vmodel = chapterLookup[str(i)]
            for slot_idx, addr in enumerate(vmodel['addresses']):
                has_text = False
                if addr.getTextFormForMS('03') != 'om.':
                    s.wordIndex03 = s.wordIndex03 + 1
                    s.word_map_03[s.wordIndex03] = str(addr.chapter_num) + ':' + str(addr.verse_num)
                    file.write(str(s.wordIndex03) + '\t' + s.word_map_03[s.wordIndex03] + '\t')
                    lastTextIndex03 = s.wordIndex03
                    has_text = True

                if has_text:
                    for vu in vu_stack_03:
                        reading = vu.getReadingForManuscript('03')
                        if not reading or reading.getDisplayValue() == 'om.':
                            vu.word_index_03 = lastTextIndex03
                        else:
                            vu.word_index_03 = s.wordIndex03
                    vu_stack_03 = []

                for vu in addr.variation_units:
                    if has_text:
                        vu.word_index_03 = s.wordIndex03
                    else:
                        vu_stack_03.append(vu)

                has_text = False
                if addr.getTextFormForMS('05') != 'om.':
                    s.wordIndex05 = s.wordIndex05 + 1
                    s.word_map_05[s.wordIndex05] = str(addr.chapter_num) + ':' + str(addr.verse_num)
                    file.write(str(s.wordIndex05) + '\t' + s.word_map_05[s.wordIndex05] + '\n')
                    lastTextIndex05 = s.wordIndex05
                    has_text = True

                if has_text:
                    for vu in vu_stack_05:
                        reading = vu.getReadingForManuscript('05')
                        if not reading or reading.getDisplayValue() == 'om.':
                            vu.word_index_05 = lastTextIndex05
                        else:
                            vu.word_index_05 = s.wordIndex05
                    vu_stack_05 = []

                for vu in addr.variation_units:
                    if has_text:
                        vu.word_index_05 = s.wordIndex05
                    else:
                        vu_stack_05.append(vu)
        file.close()

        cache_03 = c.get('variantDataCacheDir') + 'words-03-cache.json'
        jdata = json.dumps(s.word_map_03, ensure_ascii=False)
        file = open(cache_03, 'w+')
        file.write(jdata.encode('UTF-8'))
        file.close()

        cache_05 = c.get('variantDataCacheDir') + 'words-05-cache.json'
        jdata = json.dumps(s.word_map_05, ensure_ascii=False)
        file = open(cache_05, 'w+')
        file.write(jdata.encode('UTF-8'))
        file.close()
