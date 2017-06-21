#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json

class  TextFormGroup(object):

    def __init__(s, mform):
        # canonical form
        s.mainForm = mform

        # morphology data
        s.textForms = []

        # linked manuscripts
        s.linked_mss = []

    def jsonSerialize(s):
        return { '_type': 'textFormGroup', 'mainForm': s.mainForm, 'textForms': s.textForms }

    def getForm(s):
        return s.mainForm

    def initMSS(s):
        s.linked_mss = []
        for frm in s.textForms:
            s.linked_mss.append(frm.linked_mss)
