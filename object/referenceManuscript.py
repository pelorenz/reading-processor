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
        