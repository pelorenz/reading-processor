#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json

from object.readingGroup import *

def r_compare(r1, r2):
    if len(r1.manuscripts) > len(r2.manuscripts):
        return -1
    elif len(r2.manuscripts) > len(r1.manuscripts):
        return 1
    else:
        return 0

class  VariationUnit(object):

    def __init__(s, lbl, hasRetro):
        # display label
        s.label = lbl

        # Greek text has unambiguous Latin rendering?
        s.hasRetroversion = hasRetro

        # readings
        s.readings = []

        # first address of variant
        s.startingAddress = None

        # correctors - not in model! (see Reading)
        s.bezae_correctors = {}
        s.sinai_correctors = {}

        # word indices per ref MSS
        s.word_index_03 = 0
        s.word_index_05 = 0

    def jsonSerialize(s):
        return { '_type': 'variationUnit', 'label': s.label, 'hasRetroversion': s.hasRetroversion, 'readings': s.readings, 'widx03': s.word_index_03, 'widx05': s.word_index_05 }

    def isSingular(s):
        nonSing = 0
        for reading in s.readings:
            if len(reading.manuscripts) > 1:
                nonSing = nonSing + 1
        return nonSing == 1

    def getSingularMSS(s):
        mss = []
        for reading in s.readings:
            if len(reading.manuscripts) == 1:
                mss.append(reading.manuscripts[0])
        return mss

    def isReferenceSingular(s, ms):
        reading = s.getReadingForManuscript(ms)
        if reading and len(reading.manuscripts) == 1:
            return True

        if reading and ms == '05':
            if reading.hasManuscript('VL5') and len(reading.manuscripts) == 2:
                return True

        return False

    # any vu with at least 3 non-singular readings
    def isMultiple(s):
        nonSing = 0
        for reading in s.readings:
            if len(reading.manuscripts) <= 1:
                continue

            if len(reading.manuscripts) == 2 and reading.hasManuscript('05') and reading.hasManuscript('VL5'):
                continue

            nonSing = nonSing + 1

        return nonSing > 2

    def toApparatusString(s):
        app_str = ''
        for reading in s.readings:
            if len(app_str):
                app_str = app_str + ' '
            app_str = app_str + reading.toApparatusString()
        return app_str

    def getReadingSnippet(s, rdg):
        snippet = rdg.getDisplayValue()
        if len(snippet) > 50:
            snippet = snippet[:47] + '...'
        return snippet

    def getExcerpt(s, ref_rdg, witnesses, ignoreWitnesses):
        excerpt = s.getReadingSnippet(ref_rdg)

        s_readings = sorted(s.readings, cmp=r_compare)
        counter = 0
        for rdg in s_readings:
            if rdg.getDisplayValue() == ref_rdg.getDisplayValue():
                continue

            # Is reading attested by any of the relevant witnesses?
            if not ignoreWitnesses and not rdg.hasManuscripts(witnesses):
                continue

            if len(excerpt) > 0:
                excerpt = excerpt + ' | '
            if counter > 1: # max 2 additional readings
                excerpt = excerpt + 'etc'
                break;
            excerpt = excerpt + s.getReadingSnippet(rdg)
            counter = counter + 1

        return excerpt

    def getReadingForCorrector(s, c_code):
        ms = c_code[:2]
        corrector = c_code[2:]
        if ms == '01':
            for reading in s.readings:
                if corrector in reading.sinai_correctors:
                    return reading
        elif ms == '05':
            for reading in s.readings:
                if corrector in reading.bezae_correctors:
                    return reading

        return None

    def getReadingForManuscript(s, ms):
        for reading in s.readings:
            if reading.hasManuscript(ms):
                return reading
        return None

    def getSubReadingForManuscript(s, ms):
        for reading in s.readings:
            if type(reading) is ReadingGroup:
                for sub_rdg in reading.readings:
                    if sub_rdg.hasManuscript(ms):
                        return sub_rdg
            else:
                if reading.hasManuscript(ms):
                    return reading
        return None

    def getExtantManuscripts(s):
        extant_mss = []
        for reading in s.readings:
            extant_mss.extend(reading.manuscripts)
        return extant_mss

    def isLatinOnly(s):
        counter = 0
        for reading in s.readings:
            if reading.hasGreekManuscript():
                counter = counter + 1
            if counter > 1:
                return False
        return True
