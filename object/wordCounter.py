#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, string, itertools, copy, json

from object.util import *

from utility.config import *

class WordCounter:

    INDEX_MS = '05'

    def __init__(s, config):
        s.config = config
        s.wordIndex = 0

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info) 

    def computeIndexes(s, chapterLookup):
        c = s.config = Config('processor-config.json')
        s.info('Computing word indexes')

        lastTextIndex = 0
        vu_stack = []

        file = open(c.get('outputFolder') + 'word-counter.log', 'w+')
        for i in range(1, 17):
            vmodel = chapterLookup[str(i)]
            for slot_idx, addr in enumerate(vmodel['addresses']):
                has_text = False
                if addr.getTextFormForMS(WordCounter.INDEX_MS) != 'om.':
                    s.wordIndex = s.wordIndex + 1
                    file.write(str(s.wordIndex) + '\n')
                    lastTextIndex = s.wordIndex
                    has_text = True

                if has_text:
                    for vu in vu_stack:
                        reading = vu.getReadingForManuscript(WordCounter.INDEX_MS)
                        if not reading or reading.getDisplayValue() == 'om.':
                            vu.word_index = lastTextIndex
                        else:
                            vu.word_index = s.wordIndex
                    vu_stack = []

                for vu in addr.variation_units:
                    if has_text:
                        vu.word_index = s.wordIndex
                    else:
                        vu_stack.append(vu)
        file.close()