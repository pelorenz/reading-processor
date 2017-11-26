#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json
from util import *

class  ReadingGroup(object):

    def __init__(s, dvalue):
        # canonical form
        s.displayValue = dvalue

        # morphology data
        s.readings = []

        # manuscripts
        s.manuscripts = []

        # synoptic parallels
        s.synopticParallels = []

    def jsonSerialize(s):
        return { '_type': 'readingGroup', 'displayValue': s.displayValue, 'readings': s.readings, 'manuscripts': s.manuscripts, 'synopticParallels': s.synopticParallels }

    def hasManuscript(s, id):
        for ms in s.manuscripts:
            if ms == id:
                return True
        return False

    def hasManuscripts(s, ids):
        return set(s.manuscripts) & set(ids) > 0

    def getFirstGreekManuscript(s):
        mss = sorted(s.manuscripts, cmp=sortMSS)
        for ms in mss:
            if ms != '19A' and ms != 'vg' and ms[:1] != 'V' and ms not in Util.MS_OVERLAYS:
                return ms
        return None

    def hasGreekManuscript(s):
        for reading in s.readings:
            if reading.hasGreekManuscript():
                return True
        return False

    def countNonRefGreekManuscripts(s, refMS, indiv_mss):
        counter = 0
        for reading in s.readings:
            counter = counter + reading.countNonRefGreekManuscripts(refMS, indiv_mss)
        return counter

    def countNonRefGreekManuscriptsByGroup(s, refMS, msGroups, g_counts):
        counter = 0
        for reading in s.readings:
            counter = counter + reading.countNonRefGreekManuscriptsByGroup(refMS, msGroups, g_counts)
        return counter

    def hasLatinManuscript(s):
        for reading in s.readings:
            if reading.hasLatinManuscript():
                return True
        return False

    def countNonRefLatinManuscripts(s, refMS):
        counter = 0
        for reading in s.readings:
            counter = counter + reading.countNonRefLatinManuscripts(refMS)
        return counter

    def getManuscriptReading(s, ms):
        for reading in s.readings:
            if reading.hasManuscript(ms):
                return reading
        return None

    def toApparatusString(s):
        mss_str = ''
        if len(s.manuscripts):
            mss_str = s.getDisplayValue() + '] ' + mssListToString(s.manuscripts)

        return mss_str

    def getDisplayValue(s):
        first_greek = s.getFirstGreekManuscript()
        if s.displayValue != 'om.' and re.search(r'[A-Za-z]{1,}', s.displayValue) and first_greek:
            # choose Greek reading
            return s.getManuscriptReading(first_greek).getDisplayValue()

        return s.displayValue

    def getAllTokens(s):
        values = []
        for reading in s.readings:
            values.extend(reading.getAllTokens())
        return list(set(values))

    def getParallels(s):
        parallels = ''
        for p in s.synopticParallels:
            if p.text == '{NA}':
                continue
            if len(parallels) > 0:
                parallels = parallels + u', '
            parallels = parallels + p.getSummary()
        return parallels

    def isNA(s):
        is_na = False
        for p in s.synopticParallels:
            if 'NA' in p.text:
                is_na = True
            else:
                is_na = False
                break
        return is_na

    def getSynopticReadings(s):
        readings = ''
        for p in s.synopticParallels:
            if p.text == '{NA}':
                continue

            if len(readings) > 0:
                readings = readings + ' | '
            readings = readings + p.text + u' {' + str(p) + u'}'
        return readings
