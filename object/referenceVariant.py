#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json

class  ReferenceVariant(object):

    def __init__(s, vu, rdg, refms):
        # underlying variation unit
        s.variationUnit = vu

        # reading attested by reference MS
        s.reading = rdg

        # Reference manuscript
        s.referenceMS = refms

        # true-false vector of support among all witnesses for reference MS reading
        s.allVect = []

        # true-false vector of support among selected reference witnesses (Greek and Latin) for reference MS reading
        s.selVect = []

        # true-false vector of support among selected reference witnesses (Greek only) for reference MS reading
        s.selGrVect = []

    def jsonSerialize(s):
        return { '_type': 'referenceVariant', 'manuscripts': s.manuscripts }

    def shortLabel(s):
        return s.variationUnit.label

    def mediumLabel(s, witnessString):
        return s.shortLabel() + ' ' + witnessString

    def longLabel(s, witnessString, witnesses):
        return s.shortLabel() + ' ' + s.variationUnit.getExcerpt(s.referenceMS, witnesses, False) + ' ' + witnessString
