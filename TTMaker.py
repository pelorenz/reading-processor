#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, json, re

from object.jsonDecoder import *
from object.rangeManager import *
from object.referenceManuscript import *
from object.referenceVariant import *
from object.truthTable import *
from object.util import *

from utility.options import *
from utility.config import *

class TTMaker:

    def __init__(s):
        s.tt = TruthTable()

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print info

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = s.tt.config = Config(o.config)

        if o.range:
            s.tt.range_id = o.range
        else:
            s.tt.range_id = c.get('defaultRange')

        if o.refMSS:
            s.tt.refMS_IDs = o.refMSS.split(',')
        else:
            s.tt.refMS_IDs = c.get('referenceMSS')

        if o.qcaSet:
            s.tt.qcaSet = o.qcaSet
        else:
            s.tt.qcaSet = c.get('qcaSet')

        is_refresh = False
        if o.refreshCache:
            is_refresh = True

        # load variant data
        s.tt.rangeMgr = RangeManager()
        s.tt.rangeMgr.load(is_refresh)

        s.tt.variantModel = s.tt.rangeMgr.getModel(s.tt.range_id)

        s.tt.generate()

        s.info('Done')

# Invoke via entry point
# TTMaker.py -v -a c15-16 -R 05
TTMaker().main(sys.argv[1:])
