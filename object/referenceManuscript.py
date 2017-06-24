#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json

class  ReferenceManuscript(object):

    def __init__(s, ga):
        # display text
        s.gaNum = ga

        # list of variationUnit
        s.singular = []

        # various buckets for referenceVariant

        # variants by full range of witnesses (Greek and Latin)
        s.all_G = []
        s.all_GL = []

        # full range of witnesses
        s.allMSS = []
        s.allGrMSS = []

        # Null attestations per witness
        s.all_nils = {}
        s.allGr_nils = {}

        # variants by select witnesses (Greek and Latin)
        s.sel_G = []
        s.sel_GL = []

        # select witnesses
        s.selMSS = []
        s.selGrMSS = []

        # Null attestations per witness
        s.sel_nils = {}
        s.selGr_nils = {}

    def jsonSerialize(s):
        return { '_type': 'referenceManuscript', 'gaNum': s.gaNum, 'singularReadings': s.singular, 'allG': s.all_G, 'allGL': s.all_GL, 'selG': s.sel_G , 'selGL': s.sel_GL }

    def getLayer(s, var):
        rdg = var.variationUnit.getReadingForManuscript(s.gaNum)

        greek_counter = 0
        latin_counter = 0
        has35 = False
        for ms in rdg.manuscripts:
            if ms[0] == 'V' or ms[0] == 'v':
                latin_counter = latin_counter + 1
            else:
                greek_counter = greek_counter + 1
                if ms == '35':
                    has35 = True

        layer = 2
        if has35:
            layer = 1
        elif latin_counter >= greek_counter and latin_counter > 2 and greek_counter <= 3:
            layer = 3
        else:
            if latin_counter >= greek_counter and latin_counter > 1 and greek_counter <= 2:
                layer = 3
            elif latin_counter >= greek_counter and latin_counter > 0 and greek_counter <= 1:
                layer = 3

        return layer
