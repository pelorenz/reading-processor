#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, re

from object.jsonEncoder import *
from object.rangeManager import *

from utility.config import *
from utility.options import *

class VariantFinder:

    def __init__(s):
        s.range_id = ''
        s.rangeMgr = None
        s.variantModel = None
        s.binaryVariants = { "variant_count": 0, "variant_list": [] }
        s.multipleVariants = { "variant_count": 0, "variant_list": [] }

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def findMultiwayVariants(s):
        c = s.config

        for addr in s.variantModel['addresses']:
            for vu in addr.variation_units:
                if not vu.startingAddress:
                    vu.startingAddress = addr

                # exclude singulars
                if vu.isSingular():
                    continue

                v_wrapper = {}
                v_wrapper['label'] = vu.label
                v_wrapper['variation_unit'] = vu
                v_wrapper['multiple_readings'] = []
                c_groups = c.get('coreGroups')
                for reading in vu.readings:
                    r_wrapper = {}
                    r_wrapper['displayValue'] = reading.getDisplayValue()
                    r_wrapper['manuscripts'] = sorted(reading.manuscripts, cmp=sortMSS)
                    r_wrapper['witnesses'] = []

                    w_sum = ''
                    for group in c_groups:
                        g_wrapper = {}
                        g_wrapper['witness_group'] = group
                        g_wrapper['supporting_witnesses'] = []

                        is_core_group = False
                        for ms in group['members']:
                            if reading.hasManuscript(ms):
                                g_wrapper['supporting_witnesses'].append(ms)

                        if len(group['members']) > 1:
                            min_occurs = group['minOccurs']
                            if len(g_wrapper['supporting_witnesses']) >= min_occurs:
                                is_core_group = True
                        elif len(g_wrapper['supporting_witnesses']) >= 1:
                            is_core_group = True

                        if is_core_group:
                            if len(w_sum) > 0:
                                w_sum = w_sum + ' '
                            w_sum = w_sum + group['name']
                            r_wrapper['witnesses'].append(g_wrapper)

                    if len(r_wrapper['witnesses']) > 0:
                        r_wrapper['witness_summary'] = w_sum
                        v_wrapper['multiple_readings'].append(r_wrapper)

                v_wrapper['multiple_count'] = len(v_wrapper['multiple_readings'])
                if len(v_wrapper['multiple_readings']) > 2:
                    s.multipleVariants['variant_list'].append(v_wrapper)

                if len(v_wrapper['multiple_readings']) > 1:
                    s.binaryVariants['variant_list'].append(v_wrapper)

        s.multipleVariants['variant_count'] = len(s.multipleVariants['variant_list'])
        s.binaryVariants['variant_count'] = len(s.binaryVariants['variant_list'])

    def saveResults(s):
        c = s.config

        # ensure output directory exists
        finderDir = c.get('finderFolder')
        if not os.path.exists(finderDir):
            os.makedirs(finderDir)

        resultFile = finderDir + '/' + s.range_id + '-multiple-variants.json'
        jdata = json.dumps(s.multipleVariants, cls=ComplexEncoder, ensure_ascii=False)
        with open(resultFile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

        resultFile = finderDir + '/' + s.range_id + '-binary-variants.json'
        jdata = json.dumps(s.binaryVariants, cls=ComplexEncoder, ensure_ascii=False)
        with open(resultFile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        if o.range:
            s.range_id = o.range
        else:
            s.range_id = c.get('defaultRange')

        # load variant data
        s.rangeMgr = RangeManager()
        s.rangeMgr.load()

        s.variantModel = s.rangeMgr.getModel(s.range_id)

        s.findMultiwayVariants()
        s.saveResults()

        s.info('Done')

# Invoke via entry point
# variantFinder.py -v -a c01
VariantFinder().main(sys.argv[1:])
