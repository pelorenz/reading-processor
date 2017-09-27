#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json

class  Reading(object):

    def __init__(s, dvalue):
        # display text
        s.displayValue = dvalue

        # supporting witnesses
        s.manuscripts = []

        # constituent word addresses
        s.readingUnits = []

    def jsonSerialize(s):
        return { '_type': 'reading', 'displayValue': s.displayValue, 'manuscripts': s.manuscripts, 'readingUnits': s.readingUnits }

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