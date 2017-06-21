#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json

class  ReadingGroup(object):

    def __init__(s, dvalue):
        # canonical form
        s.displayValue = dvalue

        # morphology data
        s.readings = []

        # manuscripts
        s.manuscripts = []

    def jsonSerialize(s):
        return { '_type': 'readingGroup', 'displayValue': s.displayValue, 'readings': s.readings, 'manuscripts': s.manuscripts }

    def hasManuscript(s, id):
        for ms in s.manuscripts:
            if ms == id:
                return True
        return False

    def hasManuscripts(s, ids):
        return set(s.manuscripts) & set(ids) > 0

    def getDisplayValue(s):
        return s.displayValue
