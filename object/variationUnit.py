#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json

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

    def jsonSerialize(s):
        return { '_type': 'variationUnit', 'label': s.label, 'hasRetroversion': s.hasRetroversion, 'readings': s.readings }

    def isSingular(s):
        nonSing = 0
        for reading in s.readings:
            if len(reading.manuscripts) > 1:
                nonSing = nonSing + 1
        return nonSing == 1

    def isReferenceSingular(s, ms):
        reading = s.getReadingForManuscript(ms)
        if reading and len(reading.manuscripts) == 1:
            return True

        if reading and ms == '05':
            if reading.hasManuscript('VL5') and len(reading.manuscripts) == 2:
                return True

        return False

    def getReadingSnippet(s, rdg):
        snippet = rdg.getDisplayValue()
        if len(snippet) > 50:
            snippet = snippet[:47] + '...'
        return snippet

    def getExcerpt(s, refms, witnesses, ignoreWitnesses):
        ref_rdg = s.getReadingForManuscript(refms)
        #if not ref_rdg:
        #    return u''
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

    def getReadingForManuscript(s, ms):
        for reading in s.readings:
            if reading.hasManuscript(ms):
                return reading
        return None
