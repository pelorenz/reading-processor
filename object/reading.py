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
            if len(parallels) > 0:
                parallels = parallels + ','
            parallels = parallels + str(p)
        return parallels
