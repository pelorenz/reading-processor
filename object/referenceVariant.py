#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json

class  ReferenceVariant(object):

    def __init__(s, vu, rdg, refms):
        # underlying variation unit
        s.variationUnit = vu

        # reading represented by this variant
        s.reading = rdg

        # optional reading index, when each reading at variation unit has a ReferenceVariant
        s.reading_index = ''

        # Reference manuscript
        s.referenceMS = refms

        # true-false vector of support among all witnesses for reference MS reading
        s.allVect = []
        s.allGrVect = []

        # true-false vector of support among selected reference witnesses (Greek and Latin) for reference MS reading
        s.selVect = []

        # true-false vector of support among selected reference witnesses (Greek only) for reference MS reading
        s.selGrVect = []

    def jsonSerialize(s):
        return { '_type': 'referenceVariant', 'manuscripts': s.manuscripts }

    def shortLabel(s):
        return s.variationUnit.label if s.reading_index == '' else s.variationUnit.label + s.reading_index

    def mediumLabel(s, witnessString):
        return s.shortLabel() + ' ' + witnessString

    def longLabel(s, reading, witnessString, witnesses):
        return s.shortLabel() + ' ' + s.variationUnit.getExcerpt(reading, witnesses, False) + ' ' + witnessString
