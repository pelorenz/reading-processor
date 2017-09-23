#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, re

from object.rangeManager import *
from object.reading import *
from object.readingGroup import *
from object.readingUnit import *
from object.textForm import *
from object.textFormGroup import *

from utility.config import *
from utility.options import *

class MissingVariantFinder:

    def __init__(s):
        s.range_id = ''
        s.rangeMgr = None
        s.variantModel = None

        s.addrLookup = {}
        s.missing_variants = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def getAddrKey(s, addr):
        return str(addr.chapter_num) + '-' + str(addr.verse_num) + '-' + str(addr.addr_idx)

    def hasEnoughMSS(s, m_list):
        g_counter = 0
        for ms in m_list:
            if ms[:2] != 'VL' and ms != '19A' and ms != 'vg':
                g_counter = g_counter + 1

            if g_counter > 1:
                return True

        return False

    def getMissingVariant(s, addr):
        m_variant = {
          'id': str(addr.chapter_num) + ':' + str(addr.verse_num) + '.' + str(addr.addr_idx),
          'text_forms': []
        }
        if len(addr.sorted_text_forms) < 2:
            return None

        for t_form in addr.sorted_text_forms:
            text = ''
            m_list = []
            if type(t_form) is TextFormGroup:
                text = t_form.mainForm
                for lst in t_form.linked_mss:
                    m_list.extend(lst)
            else:
                text = t_form.form
                m_list= t_form.linked_mss

            m_form = {
                'mss': ' '.join(m_list),
                'text': text
            }
            if s.hasEnoughMSS(t_form.linked_mss):
                m_variant['text_forms'].append(m_form)

        if len(m_variant['text_forms']) > 1:
            return m_variant

        return None

    def findMissingVariants(s):
        c = s.config

        for addr in s.variantModel['addresses']:
            addr_key = s.getAddrKey(addr)
            if len(addr.variation_units) > 0:
                for vu in addr.variation_units:
                    reading = vu.readings[0]
                    if type(reading) is ReadingGroup:
                        reading = reading.readings[0]
    
                    r_units = reading.readingUnits
                    for ru in r_units:
                        r_key = s.getAddrKey(ru)
                        s.addrLookup[r_key] = r_key
            elif s.addrLookup.has_key(addr_key):
                continue
            else:
                missing_var = s.getMissingVariant(addr)
                if missing_var:
                    s.missing_variants.append(missing_var)
            
    def saveResults(s):
        c = s.config

        # ensure output directory exists
        finderDir = c.get('finderFolder')
        if not os.path.exists(finderDir):
            os.makedirs(finderDir)

        resultFile = finderDir + '/' + s.range_id + '-missing-variants.json'
        jdata = json.dumps(s.missing_variants, ensure_ascii=False)
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

        s.findMissingVariants()
        s.saveResults()

        s.info('Done')

# Invoke via entry point
# variantFinder.py -v -a c01-16
MissingVariantFinder().main(sys.argv[1:])
