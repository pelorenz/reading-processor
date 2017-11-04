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
        s.binaryVariantsDL = { "variant_count": 0, "variant_list": [] }
        s.multipleVariants = { "variant_count": 0, "variant_list": [] }

        s.refMS_IDs = []
        s.refMS = None # choose first ID

        s.latinLayerVariants = []

        s.addrLookup = {}
        s.layer = 'L'
        s.queryCriteria = None
        s.finderMatches = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def getAddrKey(s, addr):
        return str(addr.chapter_num) + '-' + str(addr.verse_num) + '-' + str(addr.addr_idx)

    def lookupAddr(s, slot):
        return s.addrLookup[s.getAddrKey(slot)]

    def initAddrLookup(s):
        s.info('Initializing address map')
        for addr in s.variantModel['addresses']:
            s.addrLookup[s.getAddrKey(addr)] = addr

    def computeLayer(s, var_label, reading, greek_mss, latin_mss, NEW_LAYER_CODES):
        if not NEW_LAYER_CODES:
            if reading.hasManuscript('35'):
                return 'M'
            elif var_label in s.latinLayerVariants:
                return 'L'

            return 'D'
        else:
            if reading.hasManuscript('35'):
                return 'M'
            elif var_label in s.latinLayerVariants:
                return 'L'

            return 'G'

        #for ms in reading.manuscripts:
        #    if ms == s.refMS:
        #        continue

        #    if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
        #        if ms[:2] == 'VL': ms = ms[2:]
        #        latin_mss.append(ms)
        #    else:
        #        greek_mss.append(ms)

        #return 'L' if isLatinLayer(len(greek_mss), len(latin_mss)) else 'D'

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

    def isIntersection(s, criteria_key, text_forms):
        if not s.queryCriteria.has_key(criteria_key) or len(s.queryCriteria[criteria_key]) == 0:
            return True

        values = []
        for key, val in enumerate(text_forms[criteria_key]):
            if text_forms[criteria_key].has_key(key):
                values.extend(text_forms[criteria_key][key])
        return len(set(s.queryCriteria[criteria_key]) & set(values)) > 0

    def isSubset(s, criteria_key, text_forms):
        if not s.queryCriteria.has_key(criteria_key) or len(s.queryCriteria[criteria_key]) == 0:
            return True

        values = []
        for key, val in enumerate(text_forms[criteria_key]):
            if text_forms[criteria_key].has_key(key):
                values.extend(text_forms[criteria_key][key])
        return len(set(s.queryCriteria[criteria_key]) - set(values)) == 0

    def findCriteria(s):
        c = s.config

        s.info('Finding variants')

        # ensure output directory exists
        finderDir = c.get('finderFolder')
        if not os.path.exists(finderDir):
            os.makedirs(finderDir)

        csvFile = finderDir + '/' + s.queryCriteria['result_file'] + '.csv'
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

                    latin_mss = []
                    greek_mss = []
                    layer = s.computeLayer(vu.label, r_reading, greek_mss, latin_mss, False)
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

                            csv_file.write((r_summary['displayValue'] + u'\t' + r_summary['manuscripts'] + u'\n').encode('UTF-8'))

                            v_summary['readings'].append(r_summary)
                        s.finderMatches.append(v_summary)

            csv_file.close()

        jsonFile = finderDir + '/' + s.queryCriteria['result_file'] + '.json'
        jdata = json.dumps(s.finderMatches, ensure_ascii=False)
        with open(jsonFile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

    def findMultiwayVariants(s):
        c = s.config

        s.info('Finding multiway variants')
        for addr in s.variantModel['addresses']:
            for vu in addr.variation_units:
                if not vu.startingAddress:
                    vu.startingAddress = addr

                # exclude singulars
                if vu.isSingular():
                    continue

                is_DL_layer = False

                v_wrapper = {}
                v_wrapper['label'] = vu.label
                v_wrapper['variation_unit'] = vu
                v_wrapper['multiple_readings'] = []
                c_groups = c.get('coreGroups')
                for reading in vu.readings:
                    # determine layer in ref MS
                    if reading.hasManuscript(s.refMS) and not reading.hasManuscript('35'):
                        is_DL_layer = True

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

                    if is_DL_layer:
                        s.binaryVariantsDL['variant_list'].append(v_wrapper)

        s.multipleVariants['variant_count'] = len(s.multipleVariants['variant_list'])
        s.binaryVariants['variant_count'] = len(s.binaryVariants['variant_list'])
        s.binaryVariantsDL['variant_count'] = len(s.binaryVariantsDL['variant_list'])

    def saveMultiwayVariants(s):
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

        resultFile = finderDir + '/' + s.range_id + '-binaryDL-variants.json'
        jdata = json.dumps(s.binaryVariantsDL, cls=ComplexEncoder, ensure_ascii=False)
        with open(resultFile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

    def generateHarmonizationTemplate(s):
        c = s.config
        s.info('Generating harmonization template')

        msOverlays = c.get('msOverlays')
        greekMSS = c.get('greekMSS')
        latinMSS = c.get('latinMSS')

        # letters[3] == 'c'
        letters = dict(enumerate(string.ascii_lowercase, 1))

        csvFile = c.get('finderFolder') + '/' + s.refMS + '-harmonization-template.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write('reading_id\tsort_id\treading_text\tis_singular\tlayer')
            for ms in msOverlays:
                csv_file.write('\t' + ms)
            for ms in greekMSS:
                csv_file.write('\t' + ms)
            for ms in latinMSS:
                csv_file.write('\t' + ms)
            csv_file.write('\n')
            for addr in s.variantModel['addresses']:
                for vu in addr.variation_units:
                    if not vu.startingAddress:
                        vu.startingAddress = addr

                    r_layer = ''
                    if vu.isReferenceSingular(s.refMS):
                        r_layer = 'S'

                    r_reading = vu.getReadingForManuscript(s.refMS)
                    if not r_reading:
                        r_layer = 'NA'

                    latin_mss = []
                    greek_mss = []
                    if r_layer != 'S' and r_layer != 'NA':
                        r_layer = s.computeLayer(vu.label, r_reading, greek_mss, latin_mss, True)

                    for idx, reading in enumerate(vu.readings):
                        reading_id = vu.label + letters[idx + 1]
                        sort_id = s.generateSortLabel(vu.label) + letters[idx + 1]
                        reading_text = reading.getDisplayValue()

                        is_singular = ''
                        if len(reading.manuscripts) < 2:
                            is_singular = 'sg'

                        csv_file.write((reading_id + u'\t' + sort_id + u'\t' + reading_text + u'\t' + is_singular + u'\t' + r_layer).encode('UTF-8'))
                        for ms in msOverlays:
                            csv_file.write('\t' + s.getMSValue(vu, reading, ms))
                        for ms in greekMSS:
                            csv_file.write('\t' + s.getMSValue(vu, reading, ms))
                        for ms in latinMSS:
                            csv_file.write('\t' + s.getMSValue(vu, reading, ms))
                        csv_file.write((u'\n').encode('UTF-8'))

            csv_file.close()

    def getMSValue(s, vu, reading, ms):
        val = ''
        if not vu.getReadingForManuscript(ms):
            val = '-'
        else:
            val = '1' if reading.hasManuscript(ms) else '0'
        return val

    def generateSortLabel(s, label):
        s_label = ''
        nums = re.split('\.|\-|,', label)
        seps = filter(None, re.split('[0-9]{1,2}', label))
        while nums:
            num = nums.pop(0)
            if len(num) == 1:
                num = '0' + num
            sep = ''
            if seps:
                sep = seps.pop(0)
            s_label = s_label + num + sep
        return s_label

    def generateLayerApparatus(s, layer):
        c = s.config
        s.info('Generating layer apparatus')

        csvFile = c.get('finderFolder') + '/' + s.refMS + '-apparatus-' + layer + '.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write('Reference\tReadings\tReading Count\tGreek Count\tLatin Count\tMSS\tLayer\tApparatus\n')
            for addr in s.variantModel['addresses']:
                for vu in addr.variation_units:
                    if not vu.startingAddress:
                        vu.startingAddress = addr

                    r_layer = ''
                    if vu.isReferenceSingular(s.refMS):
                        if layer != 'L':
                            continue
                        #else: # DELETE THIS TEMP CODE!
                        #    continue
                        r_layer = 'S'
                    elif vu.isSingular():
                        continue

                    r_reading = vu.getReadingForManuscript(s.refMS)
                    if not r_reading:
                        continue

                    latin_mss = []
                    greek_mss = []
                    if r_layer != 'S':
                        r_layer = s.computeLayer(vu.label, r_reading, greek_mss, latin_mss, False)
                        if r_layer != layer:
                            continue

                    r_mss = mssListToString(r_reading.manuscripts)

                    all_readings = ''
                    all_readings = all_readings + r_reading.getDisplayValue()
                    for reading in vu.readings:
                        if reading == r_reading:
                            continue

                        if len(all_readings) > 0:
                            all_readings = all_readings + ' | '
                        all_readings = all_readings + reading.getDisplayValue()

                    csv_file.write((vu.label + u'\t' + all_readings + u'\t' + str(len(vu.readings)) + u'\t' + str(len(greek_mss)) + u'\t' + str(len(latin_mss)) + u'\t' + r_mss + u'\t' + r_layer + u'\t' + vu.toApparatusString() + u'\n').encode('UTF-8'))

            csv_file.close()

    def findMissingLatinVariants(s):
        c = s.config
        s.info('Finding missing layer variants')

        all_labels = {}
        for addr in s.variantModel['addresses']:
            for vu in addr.variation_units:
                all_labels[vu.label] = vu.label

        csvFile = c.get('finderFolder') + '/' + s.refMS + '-missing-L.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write('Reference\n')
            for label in s.latinLayerVariants:
                if not all_labels.has_key(label):
                    csv_file.write((label + u'\n').encode('UTF-8'))

            csv_file.close()

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        if o.refMSS:
            s.refMS_IDs = o.refMSS.split(',')
        else:
            s.refMS_IDs = c.get('referenceMSS')

        if s.refMS_IDs and len(s.refMS_IDs) > 0:
            s.refMS = s.refMS_IDs[0]

        if o.range:
            s.range_id = o.range
        else:
            s.range_id = c.get('defaultRange')

        if o.criteria:
            s.queryCriteria = c.get('queryCriteria')[o.criteria]

        if o.layer and o.layer not in ['L', 'D', 'M']:
            s.info('If specified, layer must be one of \'L\', \'D\', or \'M\'')
            return

        s.latinLayerVariants = c.get('latinLayerVariants').split(u'|')

        # load variant data
        s.rangeMgr = RangeManager()
        s.rangeMgr.load()

        s.variantModel = s.rangeMgr.getModel(s.range_id)

        if s.queryCriteria:
            s.initAddrLookup()
            s.findCriteria()
        elif o.layer:
            s.generateLayerApparatus(o.layer)
            #s.findMissingLatinVariants()
        elif o.harmonization:
            s.generateHarmonizationTemplate()
        else:
            s.findMultiwayVariants()
            s.saveMultiwayVariants()

        s.info('Done')

# Invoke via entry point
#
# Invoke with no criteria to find multiple variants
# variantFinder.py -v -a c01-16 -R 05
#
# Specify criteria to find search matches
# variantFinder.py -v -a c01-16 -R 05 -K my-criteria
#
# Generate harmonization template
# variantFinder.py -v -a c14 -R 05 -Z
VariantFinder().main(sys.argv[1:])
