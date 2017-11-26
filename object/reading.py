#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json
from util import *

class  Reading(object):

    def __init__(s, dvalue):
        # display text
        s.displayValue = dvalue

        # supporting witnesses
        s.manuscripts = []

        # constituent word addresses
        s.readingUnits = []

        # synoptic parallels
        s.synopticParallels = []

    def jsonSerialize(s):
        return { '_type': 'reading', 'displayValue': s.displayValue, 'manuscripts': s.manuscripts, 'readingUnits': s.readingUnits, 'synopticParallels': s.synopticParallels }

    def hasManuscript(s, id):
        for ms in s.manuscripts:
            if ms == id:
                return True
        return False

    def hasManuscripts(s, ids):
        return len(set(s.manuscripts) & set(ids)) > 0

    def getFirstGreekManuscript(s):
        for ms in s.manuscripts:
            if ms != '19A' and ms != 'vg' and ms[:1] != 'V':
                return ms
        return None

    def hasGreekManuscript(s):
        for ms in s.manuscripts:
            if ms in Util.MS_OVERLAYS:
                continue
            if ms != '19A' and ms != 'vg' and ms[:1] != 'V':
                return True
        return False

    def countNonRefGreekManuscripts(s, refMS, indiv_mss):
        counter = 0
        for ms in s.manuscripts:
            if refMS == ms:
                continue
            if ms in Util.MS_OVERLAYS:
                continue
            if ms != '19A' and ms != 'vg' and ms[:1] != 'V':
                indiv_mss.append(ms)
                counter = counter + 1
        return counter

    def countNonRefGreekManuscriptsByGroup(s, refMS, msGroups, g_counts):
        counter = 0
        for ms in s.manuscripts:
            if not msGroups.has_key(ms): # Latins and non-config'ed Greeks excluded
                continue
            if refMS == ms:
                continue
            if ms in Util.MS_OVERLAYS:
                continue
            if ms == '05' or ms == '79': # bilingual
                continue
            if msGroups[ms] != 'Iso' and msGroups[ms] != 'C28':
                group = msGroups[ms]
                # did we count group already?
                if not g_counts.has_key(group):
                    counter = counter + 1
                    g_counts[group] = []
                    g_counts[group].append(ms)
                else:
                    g_counts[group].append(ms)
            else:
                counter = counter + 1
        return counter

    def hasLatinManuscript(s):
        for ms in s.manuscripts:
            if ms in Util.MS_OVERLAYS:
                continue
            if ms == '19A' or ms == 'vg' or ms[:1] == 'V':
                return True
        return False

    def countNonRefLatinManuscripts(s, refMS):
        counter = 0
        for ms in s.manuscripts:
            if ms in Util.MS_OVERLAYS:
                continue
            if ms == '19A' or ms == 'vg' or ms[:1] == 'V':
                if refMS == '05' and ms == 'VL5':
                    continue
                counter = counter + 1
        return counter

    def toApparatusString(s):
        mss_str = ''
        if len(s.manuscripts):
            mss_str = s.getDisplayValue() + '] ' + mssListToString(s.manuscripts)

        return mss_str

    def getDisplayValue(s):
        if s.displayValue:
            return s.displayValue

        txt_str = ''
        isOm = True
        for ru in s.readingUnits:
            if ru.text <> 'om.':
                isOm = False
                break
        if isOm:
            return 'om.'

        for ru in s.readingUnits:
            if ru.text == 'om.':
                continue
            if len(txt_str) > 0:
                txt_str = txt_str + ' '
            txt_str = txt_str + ru.text

        return txt_str

    def getAllTokens(s):
        values = []
        for ru in s.readingUnits:
            values.append(ru.text)
        return values

    def getParallels(s):
        parallels = ''
        for p in s.synopticParallels:
            if 'NA' in p.text:
                continue
            if len(parallels) > 0:
                parallels = parallels + u', '
            parallels = parallels + p.getSummary()
        return parallels

    def isNA(s):
        is_na = False
        for p in s.synopticParallels:
            if p.text == '{NA}':
                is_na = True
            else:
                is_na = False
                break
        return is_na

    def getSynopticReadings(s):
        readings = ''
        for p in s.synopticParallels:
            if len(readings) > 0:
                readings = readings + ' | '
            readings = readings + p.text + u' {' + str(p) + u'}'
        return readings
