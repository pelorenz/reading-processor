#! python2.7
# -*- coding: utf-8 -*-

import web, sys, os, string, re

from object.jsonEncoder import *
from object.rangeManager import *
from object.textForm import *
from object.util import *

from utility.config import *
from utility.options import *

class QueryEngine:

    def __init__(s):
        s.config = c = Config('processor-config.json')

        s.range_id = c.get('defaultRange')

        if not web.variantModel:
            rangeMgr = RangeManager()
            rangeMgr.load(False)
            web.variantModel = rangeMgr.getModel(s.range_id)
        s.variantModel = web.variantModel

        if not web.morphCache:
            web.debug('Loading morph cache')
            m_data = ''
            cachefile = c.get('cacheFolder') + c.get('morphCache')
            with open(cachefile, 'r') as file:
                m_data = file.read().decode('utf-8')
                file.close()
            web.morphCache = json.loads(m_data)
        TextForm.morph_cache = web.morphCache

        s.refMS = None # choose first ID

        s.addrLookup = {}
        s.initAddrLookup()

        s.queryCriteria = None
        s.queryMatches = []

        # stats
        s.stats_data = {}
        s.stats_data['D_instances'] = {}
        s.stats_data['L_instances'] = {}

        s.stats_data['D_lac'] = {}
        s.stats_data['L_lac'] = {}

        s.stats_data['D_readings'] = []
        s.stats_data['L_readings'] = []

        s.stats_data['latin_mss'] = []
        s.stats_data['greek_mss'] = []
        s.stats_data['latin_mss_Lsort'] = []
        s.stats_data['greek_mss_Lsort'] = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        web.debug(info)

    def computeStats(s):
        for ms in s.variantModel['manuscripts']:
            if ms == s.refMS:
                continue

            msdat = {}
            msdat['manuscript'] = ms

            # L layer stats
            msdat['L_instance_count'] = 0
            if s.stats_data['L_instances'].has_key(ms):
                msdat['L_instance_count'] = len(s.stats_data['L_instances'][ms])

            msdat['L_lac_count'] = 0
            if s.stats_data['L_lac'].has_key(ms):
                msdat['L_lac_count'] = len(s.stats_data['L_lac'][ms])

            msdat['L_count'] = len(s.stats_data['L_readings']) - msdat['L_lac_count']

            ratio = 0.0
            if msdat['L_count']:
                ratio = msdat['L_instance_count'] * 1.0 / msdat['L_count']
                ratio = round(ratio, 3)
            msdat['L_ratio'] = ratio

            # D layer stats
            msdat['D_instance_count'] = 0
            if s.stats_data['D_instances'].has_key(ms):
                msdat['D_instance_count'] = len(s.stats_data['D_instances'][ms])

            msdat['D_lac_count'] = 0
            if s.stats_data['D_lac'].has_key(ms):
                msdat['D_lac_count'] = len(s.stats_data['D_lac'][ms])

            msdat['D_count'] = len(s.stats_data['D_readings']) - msdat['D_lac_count']

            ratio = 0.0
            if msdat['D_count']:
                ratio = msdat['D_instance_count'] * 1.0 / msdat['D_count']
                ratio = round(ratio, 3)
            msdat['D_ratio'] = ratio

            if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
                s.stats_data['latin_mss'].append(msdat)
            else:
                s.stats_data['greek_mss'].append(msdat)

            s.stats_data['greek_mss'] = sorted(s.stats_data['greek_mss'], cmp=sortHauptlisteD)
            s.stats_data['latin_mss'] = sorted(s.stats_data['latin_mss'], cmp=sortHauptlisteD)
            s.stats_data['greek_mss_Lsort'] = sorted(s.stats_data['greek_mss'], cmp=sortHauptlisteL)
            s.stats_data['latin_mss_Lsort'] = sorted(s.stats_data['latin_mss'], cmp=sortHauptlisteL)

    def getAddrKey(s, addr):
        return str(addr.chapter_num) + '-' + str(addr.verse_num) + '-' + str(addr.addr_idx)

    def lookupAddr(s, slot):
        return s.addrLookup[s.getAddrKey(slot)]

    def initAddrLookup(s):
        s.info('Initializing address map')
        for addr in s.variantModel['addresses']:
            s.addrLookup[s.getAddrKey(addr)] = addr

    def computeLayer(s, reading, latin_mss, greek_mss):
        if reading.hasManuscript('35'):
            return 'M'

        for ms in reading.manuscripts:
            if ms == s.refMS:
                continue

            if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
                if ms[:2] == 'VL': ms = ms[2:]
                latin_mss.append(ms)
            else:
                greek_mss.append(ms)

        return 'L' if isLatinLayer(len(greek_mss), len(latin_mss)) else 'D'

    def getTextForms(s, v_unit, is_lemma):
        # maps of text-form lists keyed by reading unit index
        t_forms = {
            'reading_forms': [],
            'variant_forms': []
        }

        r_reading = v_unit.getReadingForManuscript(s.refMS)
        reading_tokens = r_reading.getAllTokens()
        r_iter = r_reading if type(r_reading) is Reading else r_reading.readings[0]
        for ru in r_iter.readingUnits:
            addr = s.lookupAddr(ru)
            if is_lemma:
                t_forms['reading_forms'].extend(addr.getMatchingLemmas(reading_tokens))
                t_forms['variant_forms'].extend(addr.getAllLemmas())
            else:
                t_forms['reading_forms'].extend(addr.getMatchingForms(reading_tokens))
                t_forms['variant_forms'].extend(addr.getAllForms())

        t_forms['reading_forms'] = t_forms['reading_forms']
        t_forms['variant_forms'] = t_forms['variant_forms']

        return t_forms

    def isIntersection(s, forms_key, text_forms):
        if not s.queryCriteria.has_key(forms_key) or len(s.queryCriteria[forms_key]) == 0:
            return True

        return len(set(s.queryCriteria[forms_key]) & set(text_forms[forms_key])) > 0

    def isSubset(s, forms_key, text_forms):
        if not s.queryCriteria.has_key(forms_key) or len(s.queryCriteria[forms_key]) == 0:
            return True

        return len(set(s.queryCriteria[forms_key]) - set(text_forms[forms_key])) == 0

    def getGreekReading(s, reading):
        return ''

    def findMatches(s):
        c = s.config

        s.info('Finding variants')

        # ensure output directory exists
        finderDir = c.get('finderFolder')
        if not os.path.exists(finderDir):
            os.makedirs(finderDir)

        csvFile = finderDir + '/query-results/' + s.refMS + s.queryCriteria['generated_id'] + '.csv'
        with open(csvFile, 'w+') as csv_file:
            for addr in s.variantModel['addresses']:
                for vu in addr.variation_units:
                    if not vu.startingAddress:
                        vu.startingAddress = addr

                    # exclude singulars
                    if vu.isSingular():
                        continue

                    #if vu.isReferenceSingular(s.refMS):
                    #    continue

                    r_reading = vu.getReadingForManuscript(s.refMS)

                    if not r_reading:
                        continue

                    latin_mss = []
                    greek_mss = []
                    layer = s.computeLayer(r_reading, latin_mss, greek_mss)
                    find_layers = s.queryCriteria['layers']
                    if not layer in find_layers:
                        continue

                    if addr.chapter_num == "2" and addr.verse_num == 25 and addr.addr_idx == 34:
                        i = 0
                        j = i + 1

                    text_forms = s.getTextForms(vu, s.queryCriteria['is_lemma'])

                    if not s.queryCriteria.has_key('read_op'):
                        s.queryCriteria['read_op'] = 'and'
                    if s.queryCriteria['read_op'] == 'and':
                        has_readings = s.isSubset('reading_forms', text_forms)
                    else:
                        has_readings = s.isIntersection('reading_forms', text_forms)

                    if not s.queryCriteria.has_key('var_op'):
                        s.queryCriteria['var_op'] = 'and'
                    if s.queryCriteria['var_op'] == 'and':
                        has_variants = s.isSubset('variant_forms', text_forms) 
                    else:
                        has_variants = s.isIntersection('variant_forms', text_forms)

                    if not has_readings or not has_variants:
                        continue

                    # query results
                    v_summary = {}
                    v_summary['label'] = vu.label
                    csv_file.write((vu.label + u'\t\n').encode('UTF-8'))
                    v_summary['layer'] = layer
                    v_summary['readings'] = []
                    for reading in vu.readings:
                        r_summary = {}

                        r_summary['displayValue'] = reading.getDisplayValue()
                        r_summary['manuscripts'] = ' '.join(sorted(reading.manuscripts, cmp=sortMSS))
                        r_summary['mss_string'] = mssListToString(reading.manuscripts)

                        csv_file.write((r_summary['displayValue'] + u'\t' + r_summary['manuscripts'] + u'\n').encode('UTF-8'))

                        v_summary['readings'].append(r_summary)
                    s.queryMatches.append(v_summary)

                    # stats for D and L layers
                    reading_info = {}
                    reading_info['variant_label'] = vu.label
                    reading_info['reading_value'] = r_reading.getDisplayValue()
                    reading_info['layer'] = layer
                    reading_info['latin_mss'] = latin_mss
                    reading_info['greek_mss'] = greek_mss
                    reading_info['mss_string'] = mssListToString(r_reading.manuscripts)

                    if layer == 'L':
                        s.stats_data['L_readings'].append(reading_info)
                    elif layer == 'D':
                        s.stats_data['D_readings'].append(reading_info)

                    for ms in s.variantModel['manuscripts']:
                        if ms == s.refMS or ms == '35':
                            continue

                        # Is ms attested at this variant?
                        rdg = vu.getReadingForManuscript(ms)
                        if not rdg:
                            if layer == 'L':
                                if not s.stats_data['L_lac'].has_key(ms):
                                    s.stats_data['L_lac'][ms] = []
                                s.stats_data['L_lac'][ms].append(vu.label)
                            elif layer == 'D':
                                if not s.stats_data['D_lac'].has_key(ms):
                                    s.stats_data['D_lac'][ms] = []
                                s.stats_data['D_lac'][ms].append(vu.label)
                            continue

                        # Does ms support present reading?
                        if not r_reading.hasManuscript(ms):
                            continue

                        ms_instance = {}
                        ms_instance['variant_label'] = vu.label
                        ms_instance['reading_value'] = reading_info['reading_value']

                        if layer == 'L':
                            if not s.stats_data['L_instances'].has_key(ms):
                                s.stats_data['L_instances'][ms] = []
                            s.stats_data['L_instances'][ms].append(ms_instance)
                        elif layer == 'D':
                            if not s.stats_data['D_instances'].has_key(ms):
                                s.stats_data['D_instances'][ms] = []
                            s.stats_data['D_instances'][ms].append(ms_instance)

            csv_file.close()

        saved_query = {
            'query_name': s.queryCriteria['generated_name'],
            'ref_ms': s.refMS,
            'results': s.queryMatches
        }

        jsonFile = finderDir + '/query-results/' + s.refMS + s.queryCriteria['generated_id'] + '.json'
        jdata = json.dumps(saved_query, ensure_ascii=False)
        with open(jsonFile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

        s.computeStats()

        jsonFile = finderDir + '/query-results/' + s.refMS + s.queryCriteria['generated_id'] + '-stats.json'
        jdata = json.dumps(s.stats_data, ensure_ascii=False)
        with open(jsonFile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()
