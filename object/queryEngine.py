#! python2.7
# -*- coding: utf-8 -*-

import web, sys, os, string, re

from object.jsonEncoder import *
from object.rangeManager import *

from utility.config import *
from utility.options import *

class QueryEngine:

    def __init__(s):
        s.config = Config('processor-config.json')

        s.range_id = s.config.get('defaultRange')

        if not web.variantModel:
            rangeMgr = RangeManager()
            rangeMgr.load()
            web.variantModel = rangeMgr.getModel(s.range_id)
        s.variantModel = web.variantModel

        s.refMS = None # choose first ID

        s.addrLookup = {}
        s.initAddrLookup()

        s.queryCriteria = None
        s.queryMatches = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        web.debug(info)

    def getAddrKey(s, addr):
        return str(addr.chapter_num) + '-' + str(addr.verse_num) + '-' + str(addr.addr_idx)

    def lookupAddr(s, slot):
        return s.addrLookup[s.getAddrKey(slot)]

    def initAddrLookup(s):
        s.info('Initializing address map')
        for addr in s.variantModel['addresses']:
            s.addrLookup[s.getAddrKey(addr)] = addr

    def computeLayer(s, reading):
        if reading.hasManuscript('35'):
            return 'M'

        latin_mss = []
        greek_mss = []

        for ms in reading.manuscripts:
            if ms == s.refMS:
                continue

            if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
                if ms[:2] == 'VL': ms = ms[2:]
                latin_mss.append(ms)
            else:
                greek_mss.append(ms)

        return 'L' if isLatinLayer(len(greek_mss), len(latin_mss)) else 'D'

    def getRUTextForms(s, r_unit, ru_idx, t_forms, is_ref):
        addr = s.lookupAddr(r_unit)

        for t_form in addr.sorted_text_forms:
            if type(t_form) is TextFormGroup:
                s_forms = []
                match_form = None
                for s_form in t_form.textForms:
                    if s_form.form == r_unit.text:
                        match_form = s_form.form
                    else:
                        if s_form.form != 'om.':
                            s_forms.append(s_form.form)

                if match_form:
                    if is_ref:
                        s.appendForm(match_form, t_forms['reference_forms'], ru_idx)

                        s.extendForms(s_forms, t_forms['reading_forms'], ru_idx)
                    else:
                        s_forms.append(match_form)
                        s.extendForms(s_forms, t_forms['variant_forms'], ru_idx)
                    break
            else:
                if t_form.form == r_unit.text:
                    if is_ref:
                        if s.refMS in t_form.linked_mss:
                            s.appendForm(t_form.form, t_forms['reference_forms'], ru_idx)
                        else:
                            s.appendForm(t_form.form, t_forms['reading_forms'], ru_idx)
                    else:
                        s.appendForm(t_form.form, t_forms['variant_forms'], ru_idx)
                    break

    def appendForm(s, form, form_map, key):
        if not form_map.has_key(key):
            form_map[key] = []
        if not form in form_map[key] and form != 'om.':
            form_map[key].append(form)

    def extendForms(s, forms, form_map, key):
        if not form_map.has_key(key):
            form_map[key] = []
        form_map[key] = list(set(form_map[key]) | set(forms))

    # accepts only reading (not readingGroup)
    def getFormsFromReading(s, reading, t_forms, is_ref):
        if not type(reading) is Reading:
            return

        for idx, ru in enumerate(reading.readingUnits):
            s.getRUTextForms(ru, idx, t_forms, is_ref)

    # accepts reading or readingGroup
    def getForms(s, reading, t_forms, is_ref):
        if type(reading) is ReadingGroup:
            for s_rdg in reading.readings:
                s.getFormsFromReading(s_rdg, t_forms, is_ref)
        else:
            s.getFormsFromReading(reading, t_forms, is_ref)

    def getTextForms(s, v_unit):
        # maps of text-form lists keyed by reading unit index
        t_forms = {
            'reference_forms': {},
            'reading_forms': {},
            'variant_forms': {}
        }

        for reading in v_unit.readings:
            if len(reading.manuscripts) == 0:
                continue

            is_ref = reading.hasManuscript(s.refMS)
            s.getForms(reading, t_forms, is_ref)

        return t_forms

    def isIntersection(s, forms_key, text_forms):
        if not s.queryCriteria.has_key(forms_key) or len(s.queryCriteria[forms_key]) == 0:
            return True

        values = []
        for key, val in enumerate(text_forms[forms_key]):
            if text_forms[forms_key].has_key(key):
                values.extend(text_forms[forms_key][key])
        return len(set(s.queryCriteria[forms_key]) & set(values)) > 0

    def isSubset(s, forms_key, text_forms):
        if not s.queryCriteria.has_key(forms_key) or len(s.queryCriteria[forms_key]) == 0:
            return True

        values = []
        for key, val in enumerate(text_forms[forms_key]):
            if text_forms[forms_key].has_key(key):
                values.extend(text_forms[forms_key][key])
        return len(set(s.queryCriteria[forms_key]) - set(values)) == 0

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

                    if vu.isReferenceSingular(s.refMS):
                        continue

                    r_reading = vu.getReadingForManuscript(s.refMS)

                    if not r_reading:
                        continue

                    layer = s.computeLayer(r_reading)
                    find_layers = s.queryCriteria['layers']
                    if not layer in find_layers:
                        continue

                    text_forms = s.getTextForms(vu)

                    has_refs = s.isSubset('reference_forms', text_forms)
                    has_readings = s.isSubset('reading_forms', text_forms)
                    has_variants = s.isIntersection('variant_forms', text_forms)

                    if has_refs and has_readings and has_variants:
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
