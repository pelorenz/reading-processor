#! python2.7
# -*- coding: utf-8 -*-

import platform
import sys, os, string, re
import numpy as np
import scipy.stats as stats

from object.jsonEncoder import *
from object.rangeManager import *
from object.grouper import *

from utility.config import *
from utility.options import *

class VariantFinder:

    MAX_RANGE = 9
    def __init__(s):
        s.range_id = ''
        s.rangeMgr = None
        s.variantModel = None
        s.binaryVariants = { "variant_count": 0, "variant_list": [] }
        s.binaryVariantsDL = { "variant_count": 0, "variant_list": [] }
        s.multipleVariants = { "variant_count": 0, "variant_list": [] }

        s.refMS_IDs = []
        s.refMS = None # choose first ID

        s.latinLayerCore = []
        s.latinLayerMulti = []

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

    def checkConfig(s, ref_ms, vu, layer):
        if ref_ms != '05':
            return layer

        label = vu.label
        if layer == 'L':
            if not label in s.latinLayerCore:
                s.info('Latin core reading not in config', label)
        elif layer == 'LI':
            if not label in s.latinLayerMulti:
                s.info('Latin multi reading not in config', label)
        else:
            if label in s.latinLayerCore:
                s.info('Non-core reading in latinLayerCoreVariants', label, ', layer:', layer)
            elif label in s.latinLayerMulti:
                s.info('Non-multi reading in latinLayerMultiVariants', label, ', layer:', layer)
        if not vu.hasRetroversion:
            layer = layer + 'NR'
        return layer

    def enhancedLayer(s, layer, ref_ms, reading, indiv_mss):
        c = s.config
        msGroupAssignments = c.get('msGroupAssignments')
        indiv_mss = []
        if not indiv_mss:
            reading.countNonRefGreekManuscripts(ref_ms, indiv_mss)
        if layer == 'CC':
            for ms in indiv_mss:
                if msGroupAssignments[ms] == 'F03':
                    layer = 'CB'
                    break
        if layer == 'CC':
            for ms in indiv_mss:
                if ms == '032':
                    layer = 'CW'
                    break
        if layer == 'CC':
            layer = 'CCC'
            for ms in indiv_mss:
                if msGroupAssignments[ms] != 'C565':
                    layer = 'CC'
                    break
        return layer

    def computeLayer3(s, ref_ms, vu, reading):
        indiv_mss = []
        layer = s.computeLayer2(ref_ms, vu, reading)
        return s.enhancedLayer(layer, ref_ms, reading, indiv_mss)

    def computeLayer2(s, ref_ms, vu, reading):
        c = s.config

        if not reading:
            return s.checkConfig(ref_ms, vu, 'N') # unattested

        if vu.isReferenceSingular(ref_ms):
            return s.checkConfig(ref_ms, vu, 'S') # singular

        if reading.hasManuscript('35'):
            return s.checkConfig(ref_ms, vu, 'M') # mainstream

        g_counts = {}
        msGroupAssignments = c.get('msGroupAssignments')
        latin_count = reading.countNonRefLatinManuscripts(ref_ms)
        nonref_count = reading.countNonRefGreekManuscriptsByGroup(ref_ms, msGroupAssignments, g_counts)

        if ref_ms == '05':
            if nonref_count < VariantFinder.MAX_RANGE and latin_count >= nonref_count and latin_count != 0:
                if nonref_count == 0:
                    return s.checkConfig(ref_ms, vu, 'L') # Latin

                base_mss = []
                base_mss.append('28')
                base_mss.append('2542')
                for ms, group in msGroupAssignments.iteritems():
                    if group == 'F03' or group == 'C565' or group == 'F1' or group == 'F13':
                        base_mss.append(ms)
                if set(base_mss) & set(reading.manuscripts):
                    if reading.hasManuscript('565') or reading.hasManuscript('038') or reading.hasManuscript('700'):
                        return s.checkConfig(ref_ms, vu, 'CC') # Latin base + Cluster 565
                    if reading.hasManuscript('03'):
                        return s.checkConfig(ref_ms, vu, 'BB') # Latin base + 03
                    if reading.hasManuscript('032'):
                        return s.checkConfig(ref_ms, vu, 'WW') # Latin base + 032
                    return s.checkConfig(ref_ms, vu, 'GG') # Latin base + other
                else:
                    return s.checkConfig(ref_ms, vu, 'LI') # Latin + independent

            if reading.hasManuscript('565') or reading.hasManuscript('038') or reading.hasManuscript('700'):
                return s.checkConfig(ref_ms, vu, 'C') # Base + Cluster 565
            if reading.hasManuscript('03'):
                return s.checkConfig(ref_ms, vu, 'B') # Base + 03
            if reading.hasManuscript('032'):
                return s.checkConfig(ref_ms, vu, 'W') # 032

            indiv_mss = []
            nonref_count_indiv = reading.countNonRefGreekManuscripts(ref_ms, indiv_mss)
            if nonref_count_indiv == 1:
                return s.checkConfig(ref_ms, vu, 'SS') # subsingular individual
            if nonref_count == 1:
                for grp, g_mss in g_counts.iteritems():
                    if grp == 'Byz' or grp == 'Iso':
                        break;
                    return s.checkConfig(ref_ms, vu, 'SF') # subsingular family

            return s.checkConfig(ref_ms, vu, 'G') # Base
        else:
            if nonref_count < VariantFinder.MAX_RANGE and latin_count >= nonref_count and latin_count != 0:
                return 'L'
            else:
                return 'G'

    def computeLayer(s, var_label, reading, NEW_LAYER_CODES):
        if s.refMS == '05':
            if not NEW_LAYER_CODES:
                if reading.hasManuscript('35'):
                    return 'M'
                elif var_label in s.latinLayerCore or var_label in s.latinLayerMulti:
                    return 'L'

                return 'D'
            else:
                if reading.hasManuscript('35'):
                    return 'M'
                if var_label in s.latinLayerCore:
                    return 'L'
                if var_label in s.latinLayerMulti:
                    return 'LI'
                if reading.hasManuscript('565') or reading.hasManuscript('038') or reading.hasManuscript('700'):
                    return 'C'
                if reading.hasManuscript('03'):
                    return 'B'
                if reading.hasManuscript('032'):
                    return 'W'

                return 'G'
        else:
            for ms in reading.manuscripts:
                if ms == s.refMS:
                    continue

                if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
                    if ms[:2] == 'VL': ms = ms[2:]
                    latin_mss.append(ms)
                else:
                    greek_mss.append(ms)

            if not NEW_LAYER_CODES:
                return 'L' if isLatinLayer(len(greek_mss), len(latin_mss)) else 'D'
            else:
                return 'L' if isLatinLayer(len(greek_mss), len(latin_mss)) else 'G'

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

                    layer = s.computeLayer(vu.label, r_reading, False)
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

    def buildNonMajorityLayers(s):
        c = s.config
        s.info('Building non-majority layers by groups')

        ref_ms = s.refMS
        msGroupAssignments = c.get('msGroupAssignments')

        file_name = c.get('finderFolder') + '/bezae-nm-base-' + s.range_id + '.csv'
        file = open(file_name, 'w+')
        file.write('Sort Ref\tReference\tLayer\tReadings\tMSS\tMSS (Indiv)\tLatin Count\tGreek Count (ungrouped)\tGreek Count (grouped)\tReading Count\tGroups\tApparatus\n')
        for addr in s.variantModel['addresses']:
            for vidx, vu in enumerate(addr.variation_units):
                if not vu.startingAddress:
                    vu.startingAddress = addr

                r_reading = vu.getReadingForManuscript(ref_ms)
                r_layer = s.computeLayer2(ref_ms, vu, r_reading)
                if r_layer != 'BB' and r_layer != 'CC' and r_layer != 'GG' and r_layer != 'WW' and r_layer != 'CNR' and r_layer != 'CCNR' and r_layer != 'C' and r_layer != 'BNR' and r_layer != 'WNR' and r_layer != 'GNR':
                    continue

                indiv_mss = []
                g_counts = {}
                nonref_count = 0
                latin_count = r_reading.countNonRefLatinManuscripts(ref_ms)
                nonref_count = r_reading.countNonRefGreekManuscriptsByGroup(ref_ms, msGroupAssignments, g_counts)
                nonref_count_indiv = 0
                nonref_count_indiv = r_reading.countNonRefGreekManuscripts(ref_ms, indiv_mss)

                label = vu.label
                sort_label = s.generateSortLabel(label)
                readings_str = readingsToString(vu, r_reading)
                mss = mssListToString(r_reading.manuscripts)
                groupMSS = mssGroupListToString(r_reading.manuscripts, msGroupAssignments, g_counts, ref_ms)

                g_list = g_counts.keys()
                g_str = groupMapToString(g_counts, g_list)

                r_layer = s.enhancedLayer(r_layer, ref_ms, r_reading, indiv_mss)

                file.write((sort_label + u'\t' + label + u'\t' + r_layer + u'\t' + readings_str + u'\t' + groupMSS + u'\t' + mss + u'\t' + str(latin_count) + u'\t' + str(nonref_count_indiv) + u'\t' + str(nonref_count) + u'\t' + str(len(vu.readings)) + u'\t' + g_str + u'\t' + vu.toApparatusString() + u'\n').encode('UTF-8'))

        file.close()

    def buildLatinLayer(s):
        c = s.config
        s.info('Building Latin layer by groups')

        importLayer = {}
        jsondata = ''
        jsonfile = c.get('inputFolder') + 'latin-layer-import.json'
        if os.path.exists(jsonfile):
            with open(jsonfile, 'r') as file:
                s.info('Reading', jsonfile)
                jsondata = file.read().decode('utf-8')
                file.close()

            importLayer = json.loads(jsondata)

        ref_mss = c.get('latinLayerCountMSS')
        msGroupAssignments = c.get('msGroupAssignments')
        greekMSS = c.get('greekMSS')
        greekGroups = c.get('greekGroups')
        base_mss = []
        base_mss.append('28')
        base_mss.append('2542')
        for ms, group in msGroupAssignments.iteritems():
            if group == 'F03' or group == 'C565' or group == 'F1' or group == 'F13':
                base_mss.append(ms)

        ref_map = {}
        for ref_ms in ref_mss:
            # initialize lists of counts, lists, and maps (1-5)
            dat = {
                'l_layer_counts': {},
                'l_layer': {},
                'l_short': {},
                'sh_maps': {}
            }

            for i in range(0, VariantFinder.MAX_RANGE):
                dat['l_layer_counts'][i] = 0
                dat['l_layer'][i] = []
                dat['l_short'][i] = []
                dat['sh_maps'][i] = {}

            ref_map[ref_ms] = dat

        bz_bas_counts = {}
        bz_bas_long = {}
        bz_bas_short = {}
        bz_bas_sh_maps = {}

        bz_lat_counts = {}
        bz_lat_long = {}
        bz_lat_short = {}
        bz_lat_sh_maps = {}
        bz_lat_data = {}

        bz_sing_agreemts = {}
        bz_sing_group_agreemts = {}

        bz_lyr_map = {}
        bz_lyr_map['NONMAJORITY'] = []
        bz_lyr_map['BASE'] = []
        bz_lyr_map['LATIN'] = []
        bz_lyr_map['SINGULAR'] = []

        bz_lyr_codes = ['BASE', 'LATIN', 'SINGULAR', 'CC', 'CCNR', 'C', 'CNR', 'L', 'LI', 'S', 'SNR', 'SS', 'SSNR', 'SF', 'SFNR', 'B', 'BNR', 'BB', 'BBNR', 'W', 'WNR', 'WW', 'WWNR', 'G', 'GNR', 'GG', 'GGNR', 'NONMAJORITY']

        for i in range(0, VariantFinder.MAX_RANGE):
            bz_bas_counts[i] = 0
            bz_bas_long[i] = []
            bz_bas_short[i] = []
            bz_bas_sh_maps[i] = {}

            bz_lat_counts[i] = 0
            bz_lat_long[i] = []
            bz_lat_short[i] = []
            bz_lat_sh_maps[i] = {} # keyed to short ref
            bz_lat_data[i] = {} # keyed to long ref

        vu_count = 0
        retro_count = 0
        for idx, ref_ms in enumerate(ref_mss):
            for addr in s.variantModel['addresses']:
                for vu in addr.variation_units:
                    if not vu.startingAddress:
                        vu.startingAddress = addr

                    if idx == 0:
                        vu_count = vu_count + 1
                        if vu.hasRetroversion:
                            retro_count = retro_count + 1

                    reading = vu.getReadingForManuscript(ref_ms)
                    if not reading:
                        continue

                    indiv_mss = []
                    g_counts = {}
                    nonref_count = 0
                    latin_count = reading.countNonRefLatinManuscripts(ref_ms)
                    nonref_count = reading.countNonRefGreekManuscriptsByGroup(ref_ms, msGroupAssignments, g_counts)

                    nonref_count_indiv = 0
                    if ref_ms == '05':
                        nonref_count_indiv = reading.countNonRefGreekManuscripts(ref_ms, indiv_mss)

                    # individual singular agreements
                    if ref_ms == '05' and nonref_count_indiv == 1:
                        sg_ms = indiv_mss[0]

                        if not bz_sing_agreemts.has_key(sg_ms):
                            bz_sing_agreemts[sg_ms] = []
                        ref = str(addr.chapter_num) + ':' + str(addr.verse_num)
                        bz_sing_agreemts[sg_ms].append(ref)

                    # family singular agreements
                    if ref_ms == '05' and nonref_count == 1:
                        for grp, g_mss in g_counts.iteritems():
                            if grp == 'Byz' or grp == 'Iso':
                                break;
                            if not bz_sing_group_agreemts.has_key(grp):
                                bz_sing_group_agreemts[grp] = []

                            ref = str(addr.chapter_num) + ':' + str(addr.verse_num)
                            bz_sing_group_agreemts[grp].append(ref)
                            break

                    if ref_ms == '05':
                        lyr_cod = s.computeLayer2(ref_ms, vu, reading)
                        if not bz_lyr_map.has_key(lyr_cod):
                            bz_lyr_map[lyr_cod] = []
                        bz_lyr_map[lyr_cod].append(vu.label)
                        if lyr_cod[:1] == 'B' or lyr_cod[:1] == 'C' or lyr_cod[:1] == 'G' or lyr_cod[:1] == 'W':
                            bz_lyr_map['BASE'].append(vu.label)
                            bz_lyr_map['NONMAJORITY'].append(vu.label)
                        if lyr_cod[:1] == 'L':
                            bz_lyr_map['LATIN'].append(vu.label)
                            bz_lyr_map['NONMAJORITY'].append(vu.label)
                        if lyr_cod[:1] == 'S':
                            bz_lyr_map['SINGULAR'].append(vu.label)
                            bz_lyr_map['NONMAJORITY'].append(vu.label)

                    if nonref_count >= VariantFinder.MAX_RANGE or latin_count < nonref_count or latin_count == 0:
                        continue

                    ref_map[ref_ms]['l_layer_counts'][nonref_count] = ref_map[ref_ms]['l_layer_counts'][nonref_count] + 1
                    ref_map[ref_ms]['l_layer'][nonref_count].append(vu.label)

                    rs = re.search(r'^(\d{1,2})\.(\d{1,2})\..+$', vu.label)
                    if rs:
                        chapter = rs.group(1)
                        verse = rs.group(2)

                    ref = chapter + ':' + verse
                    if not ref_map[ref_ms]['sh_maps'][nonref_count].has_key(ref):
                        ref_map[ref_ms]['sh_maps'][nonref_count][ref] = 1
                        ref_map[ref_ms]['l_short'][nonref_count].append(ref)
                    else:
                        ref_map[ref_ms]['sh_maps'][nonref_count][ref] = ref_map[ref_ms]['sh_maps'][nonref_count][ref] + 1

                    if ref_ms == '05':
                        if set(base_mss) & set(reading.manuscripts):
                            bz_bas_counts[nonref_count] = bz_bas_counts[nonref_count] + 1
                            bz_bas_long[nonref_count].append(vu.label)
                            if not bz_bas_sh_maps[nonref_count].has_key(ref):
                                bz_bas_sh_maps[nonref_count][ref] = 1
                                bz_bas_short[nonref_count].append(ref)
                            else:
                                bz_bas_sh_maps[nonref_count][ref] = bz_bas_sh_maps[nonref_count][ref] + 1
                        else:
                            bz_lat_counts[nonref_count] = bz_lat_counts[nonref_count] + 1

                            readings_str = readingsToString(vu, reading)

                            bz_lat_long[nonref_count].append(vu.label)
                            is_bilingual = True if '79' in reading.manuscripts else False
                            r_data = {
                                'apparatusStr': vu.toApparatusString(),
                                'mss': mssListToString(reading.manuscripts),
                                'groupMSS': mssGroupListToString(reading.manuscripts, msGroupAssignments, g_counts, ref_ms),
                                'groupCounts': g_counts,
                                'isBilingual': is_bilingual,
                                'readingsDisplay': readings_str,
                                'readingCount': len(vu.readings),
                                'greekCountGrouped': nonref_count,
                                'greekCountUngrouped': nonref_count_indiv,
                                'latinCount': latin_count,
                                'layer': 'L'
                            }
                            bz_lat_data[vu.label] = r_data

                            if not bz_lat_sh_maps[nonref_count].has_key(ref):
                                bz_lat_sh_maps[nonref_count][ref] = 1
                                bz_lat_short[nonref_count].append(ref)
                            else:
                                bz_lat_sh_maps[nonref_count][ref] = bz_lat_sh_maps[nonref_count][ref] + 1

        csvFile = c.get('finderFolder') + '/bezae-layer-codes-' + s.range_id + '.csv'
        with open(csvFile, 'w+') as csv_file:
            for lyr_cod in bz_lyr_codes:
                csv_file.write(lyr_cod)
                if not bz_lyr_map.has_key(lyr_cod):
                    csv_file.write(' (0)\n\n')
                    continue
                csv_file.write(' (' + str(len(bz_lyr_map[lyr_cod])) + ')\n')
            csv_file.write('\n')
            for lyr_cod in bz_lyr_codes:
                csv_file.write(lyr_cod)
                if not bz_lyr_map.has_key(lyr_cod):
                    csv_file.write(' (0)\n')
                    continue
                csv_file.write(' (' + str(len(bz_lyr_map[lyr_cod])) + ')\n')
                for label in bz_lyr_map[lyr_cod]:
                    csv_file.write(label + '\n')
                csv_file.write('\n')
            csv_file.close()

        csvFile = c.get('finderFolder') + '/bezae-latin-layer-' + s.range_id + '.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write('Sort Ref\tLayer\tParallels Against\tParallels For\tType\tClass Description\tReference\tReadings\tMSS\tMSS (Indiv)\tLatin Count\tGreek Count (ungrouped)\tGreek Count (grouped)\tReading Count\tBilingual\tGroups\tApparatus\n')

            for i in range(0, VariantFinder.MAX_RANGE):
                for label in bz_lat_long[i]:
                    r_data = bz_lat_data[label]
                    sort_label = s.generateSortLabel(label)

                    parallels_against = ''
                    parallels_for = ''
                    r_type = ''
                    class_description = ''
                    if importLayer.has_key(label):
                        i_rdg = importLayer[label]
                        if i_rdg.has_key('parallelsAgainst'):
                            parallels_against = i_rdg['parallelsAgainst']
                        if i_rdg.has_key('parallelsFor'):
                            parallels_for = i_rdg['parallelsFor']
                        if i_rdg.has_key('type'):
                            r_type = i_rdg['type']
                        if i_rdg.has_key('desc'):
                            class_description = i_rdg['desc']
                    else:
                        class_description = 'NEW'

                    g_list = r_data['groupCounts'].keys()
                    g_str = groupMapToString(r_data['groupCounts'], g_list)

                    is_bilingual = 'b' if r_data['isBilingual'] else ''

                    csv_file.write((sort_label + u'\t' + r_data['layer'] + u'\t' + parallels_against + u'\t' + parallels_for + u'\t' + r_type + u'\t' + class_description + u'\t' + label + u'\t' + r_data['readingsDisplay'] + u'\t' + r_data['groupMSS'] + u'\t' + r_data['mss'] + u'\t' + str(r_data['latinCount']) + u'\t' + str(r_data['greekCountUngrouped']) + u'\t' + str(r_data['greekCountGrouped']) + u'\t' + str(r_data['readingCount']) + u'\t' + is_bilingual + u'\t' + g_str + u'\t' + r_data['apparatusStr'] + u'\n').encode('UTF-8'))

            csv_file.close()

        csvFile = c.get('finderFolder') + '/bezan-singular-agreements-' + s.range_id + '.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write('Manuscript\tSingular Agreements\tVerses\n')
            for sg_ms in greekMSS:
                if bz_sing_agreemts.has_key(sg_ms):
                    v_list = bz_sing_agreemts[sg_ms]
                    csv_file.write(sg_ms + '\t' + str(len(v_list)) + '\t')

                    # refListToString
                    v_str = refListToString(v_list)
                    csv_file.write(v_str + '\n')

            csv_file.write('\n')
            csv_file.write('Group\tSingular Agreements\tVerses\n')
            for sg_grp in greekGroups:
                if bz_sing_group_agreemts.has_key(sg_grp):
                    v_list = bz_sing_group_agreemts[sg_grp]
                    csv_file.write(sg_grp + '\t' + str(len(v_list)) + '\t')

                    # refListToString
                    v_str = refListToString(v_list)
                    csv_file.write(v_str + '\n')

            csv_file.close()

        csvFile = c.get('finderFolder') + '/bezan-layers-' + s.range_id + '.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write('Manuscripts\tLatin-Layer Count\tVerses\t\tVerses (long)\n')
            for i in range(0, VariantFinder.MAX_RANGE):
                csv_file.write(str(i) + '\t')
                csv_file.write(str(bz_lat_counts[i]) + '\t')

                rdg_str = ''
                for ref in bz_lat_short[i]:
                    if bz_lat_sh_maps[i].has_key(ref) and bz_lat_sh_maps[i][ref] > 1:
                        ref = ref + ' (' + str(bz_lat_sh_maps[i][ref]) + 'x)'

                    if rdg_str:
                        rdg_str = rdg_str + '; '
                    rdg_str = rdg_str + ref
                csv_file.write(rdg_str + '\t\t')

                rdg_str = ''
                for ref in bz_lat_long[i]:
                    if rdg_str:
                        rdg_str = rdg_str + '; '
                    rdg_str = rdg_str + ref
                csv_file.write(rdg_str + '\n')

            csv_file.write('\n')
            csv_file.write('Manuscripts\tBase-Layer Count\tVerses\t\tVerses (long)\n')
            for i in range(0, VariantFinder.MAX_RANGE):
                csv_file.write(str(i) + '\t')
                csv_file.write(str(bz_bas_counts[i]) + '\t')

                rdg_str = ''
                for ref in bz_bas_short[i]:
                    if bz_bas_sh_maps[i].has_key(ref) and bz_bas_sh_maps[i][ref] > 1:
                        ref = ref + ' (' + str(bz_bas_sh_maps[i][ref]) + 'x)'

                    if rdg_str:
                        rdg_str = rdg_str + '; '
                    rdg_str = rdg_str + ref
                csv_file.write(rdg_str + '\t\t')

                rdg_str = ''
                for ref in bz_bas_long[i]:
                    if rdg_str:
                        rdg_str = rdg_str + '; '
                    rdg_str = rdg_str + ref
                csv_file.write(rdg_str + '\n')

            csv_file.close()

        csvFile = c.get('finderFolder') + '/latin-layer-counts-' + s.range_id + '.csv'
        with open(csvFile, 'w+') as csv_file:
            for i in range(0, VariantFinder.MAX_RANGE):
                csv_file.write(str(i) + ' Manuscripts\n')
                csv_file.write('Manuscript\tLatin-Layer Count\tVerses\t\tVerses (long)\n')
                for ref_ms in ref_mss:
                    csv_file.write(ref_ms + '\t')
                    csv_file.write(str(ref_map[ref_ms]['l_layer_counts'][i]) + '\t')

                    rdg_str = ''
                    for ref in ref_map[ref_ms]['l_short'][i]:
                        if ref_map[ref_ms]['sh_maps'][i].has_key(ref) and ref_map[ref_ms]['sh_maps'][i][ref] > 1:
                            ref = ref + ' (' + str(ref_map[ref_ms]['sh_maps'][i][ref]) + 'x)'

                        if rdg_str:
                            rdg_str = rdg_str + '; '
                        rdg_str = rdg_str + ref
                    csv_file.write(rdg_str + '\t\t')

                    rdg_str = ''
                    for ref in ref_map[ref_ms]['l_layer'][i]:
                        if rdg_str:
                            rdg_str = rdg_str + '; '
                        rdg_str = rdg_str + ref

                    csv_file.write(rdg_str + '\n')
                csv_file.write('\n')

            csv_file.close()

        csvFile = c.get('finderFolder') + '/latin-layer-all-counts-' + s.range_id + '.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write('Counts per Manuscript\n')
            csv_file.write('Manuscript')
            for i in range(0, VariantFinder.MAX_RANGE):
                csv_file.write('\tCount ' + str(i))
            csv_file.write('\n')
            for ref_ms in ref_mss:
                csv_file.write(ref_ms)
                for i in range(0, VariantFinder.MAX_RANGE):
                    csv_file.write('\t' + str(ref_map[ref_ms]['l_layer_counts'][i]))
                csv_file.write('\n')

            csv_file.write('\n')
            csv_file.write('VU Count\t' + str(vu_count) + '\n')
            csv_file.write('Retro Count\t' + str(retro_count) + '\n')
            csv_file.close()

    def generateHarmonizationTemplate(s, range_id):
        c = s.config
        s.info('Generating harmonization template')

        msOverlays = c.get('msOverlays')
        greekMSS = c.get('greekMSS')
        latinMSS = c.get('latinMSS')

        # letters[3] == 'c'
        letters = dict(enumerate(string.ascii_lowercase, 1))

        # show singulars for these MSS
        showSingulars = c.get('showSingulars')

        csvFile = c.get('finderFolder') + '/' + s.refMS + '-harmonization-template-' + range_id + '.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write('sort_id\treading_id\treading_text\tparallels\tVogels Ref\tVogels Page\tParker Page\tna28\t05\t35\tlayer_new\tlayer\tis_singular\tis_latin\tsynoptic_rdgs')
            #for ms in msOverlays: # na28
            #    csv_file.write('\t' + ms)
            for ms in greekMSS:
                if ms != '05' and ms != '35':
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
                    elif s.refMS == '05' and isSubSingular(s.config.get('subsingularVariants'), vu, s.refMS):
                        r_layer = 'SS'

                    r_reading = vu.getReadingForManuscript(s.refMS)
                    if not r_reading:
                        r_layer = 'NA'

                    if vu.isSingular():
                        sgMSS = vu.getSingularMSS()
                        if not set(sgMSS) & set(showSingulars):
                            continue

                    if r_layer != 'S' and r_layer != 'SS' and r_layer != 'NA':
                        r_layer = s.computeLayer(vu.label, r_reading, True)

                    for idx, reading in enumerate(vu.readings):
                        if not reading.manuscripts:
                            continue

                        reading_id = vu.label + letters[idx + 1]
                        sort_id = s.generateSortLabel(vu.label) + letters[idx + 1]
                        reading_text = reading.getDisplayValue()

                        is_singular = ''
                        if len(reading.manuscripts) == 1:
                            is_singular = reading.manuscripts[0]
                            if not is_singular in showSingulars:
                                continue

                        is_latin = ''
                        if not reading.hasGreekManuscript():
                            is_latin = 'la'

                        parallels = ''
                        if reading.isNA():
                            parallels = '{NA}'
                        else:
                            parallels = reading.getParallels()
                        p_readings = reading.getSynopticReadings()

                        csv_file.write((sort_id + u'\t' + reading_id + u'\t' + reading_text + u'\t' + parallels + u'\t\t\t\t\t' + s.getMSValue(vu, reading, '05') + u'\t' + s.getMSValue(vu, reading, '35') + u'\t' + r_layer + u'\t\t' + is_singular + u'\t' + is_latin + u'\t' + p_readings).encode('UTF-8'))
                        #for ms in msOverlays: # na28
                        #    csv_file.write('\t' + s.getMSValue(vu, reading, ms))
                        for ms in greekMSS:
                            if ms != '05' and ms != '35':
                                csv_file.write('\t' + s.getMSValue(vu, reading, ms))
                        for ms in latinMSS:
                            csv_file.write('\t' + s.getMSValue(vu, reading, ms))
                        csv_file.write((u'\n').encode('UTF-8'))

            csv_file.close()

    def generateCorrectorTemplate(s, range_id):
        c = s.config
        s.info('Generating corrector templates')

        greekMSS = c.get('greekMSS')
        latinMSS = c.get('latinMSS')

        # letters[3] == 'c'
        letters = dict(enumerate(string.ascii_lowercase, 1))

        csvFile = c.get('finderFolder') + '/bezae-correctors-' + range_id + '.csv'
        bez_file = open(csvFile, 'w+')

        csvFile = c.get('finderFolder') + '/sinai-correctors-' + range_id + '.csv'
        sai_file = open(csvFile, 'w+')

        for addr in s.variantModel['addresses']:
            for vu in addr.variation_units:
                if not vu.startingAddress:
                    vu.startingAddress = addr

                if not vu.sinai_correctors and not vu.bezae_correctors:
                    continue

                if vu.sinai_correctors:
                    sai_file.write(vu.label + u'\n')
                    rdg = vu.getReadingForManuscript('01')
                    if rdg:
                        sai_file.write((u'\t01*\t' + rdg.getDisplayValue() + u'\n').encode('UTF-8'))
                    else:
                        sai_file.write((u'\t01*\t---\n').encode('UTF-8'))
                    if vu.sinai_correctors.has_key('A'):
                        sai_file.write((u'\tA\t' + vu.sinai_correctors['A'] + u'\n').encode('UTF-8'))
                    if vu.sinai_correctors.has_key('C1'):
                        sai_file.write((u'\tC1\t' + vu.sinai_correctors['C1'] + u'\n').encode('UTF-8'))
                    if vu.sinai_correctors.has_key('C2'):
                        sai_file.write((u'\tC2\t' + vu.sinai_correctors['C2'] + u'\n').encode('UTF-8'))
                    sai_file.write(u'\n')

                    sai_file.write(u'sort_id\treading_id\treading_text\tA\tC1\tC2\t01\t35')
                    for ms in greekMSS:
                        if ms != '01' and ms != '35':
                            sai_file.write(u'\t' + ms)
                    for ms in latinMSS:
                        sai_file.write(u'\t' + ms)
                    sai_file.write(u'\n')

                    for idx, reading in enumerate(vu.readings):
                        if not reading.manuscripts:
                            continue

                        reading_id = vu.label + letters[idx + 1]
                        sort_id = s.generateSortLabel(vu.label) + letters[idx + 1]
                        reading_text = reading.getDisplayValue()
                        is01A = False
                        if vu.sinai_correctors.has_key('A') and reading_text == vu.sinai_correctors['A']:
                            is01A = True
                        is01C1 = False
                        if vu.sinai_correctors.has_key('C1') and reading_text == vu.sinai_correctors['C1']:
                            is01C1 = True
                        is01C2 = False
                        if vu.sinai_correctors.has_key('C2') and reading_text == vu.sinai_correctors['C2']:
                            is01C2 = True

                        sai_file.write((sort_id + u'\t' + reading_id + u'\t' + reading_text + u'\t').encode('UTF-8'))
                        if is01A:
                            sai_file.write((u'1').encode('UTF-8'))
                        sai_file.write((u'\t').encode('UTF-8'))
                        if is01C1:
                            sai_file.write((u'1').encode('UTF-8'))
                        sai_file.write((u'\t').encode('UTF-8'))
                        if is01C2:
                            sai_file.write((u'1').encode('UTF-8'))
                        sai_file.write((u'\t').encode('UTF-8'))
                        sai_file.write((s.getMSValue(vu, reading, '01') + u'\t' + s.getMSValue(vu, reading, '35')).encode('UTF-8'))

                        for ms in greekMSS:
                            if ms != '01' and ms != '35':
                                sai_file.write(u'\t' + s.getMSValue(vu, reading, ms))
                        for ms in latinMSS:
                            sai_file.write(u'\t' + s.getMSValue(vu, reading, ms))
                        sai_file.write(u'\n')

                    sai_file.write(u'\n')

                if vu.bezae_correctors:
                    bez_file.write(vu.label + u'\n')
                    rdg = vu.getReadingForManuscript('05')
                    if rdg:
                        bez_file.write((u'\t05*\t' + rdg.getDisplayValue() + u'\n').encode('UTF-8'))
                    else:
                        bez_file.write((u'\t05*\t---\n').encode('UTF-8'))
                    if vu.bezae_correctors.has_key('pm'):
                        bez_file.write((u'\tpm\t' + vu.bezae_correctors['pm'] + u'\n').encode('UTF-8'))
                    if vu.bezae_correctors.has_key('sm'):
                        bez_file.write((u'\tsm\t' + vu.bezae_correctors['sm'] + u'\n').encode('UTF-8'))
                    if vu.bezae_correctors.has_key('A'):
                        bez_file.write((u'\tA\t' + vu.bezae_correctors['A'] + u'\n').encode('UTF-8'))
                    if vu.bezae_correctors.has_key('B'):
                        bez_file.write((u'\tB\t' + vu.bezae_correctors['B'] + u'\n').encode('UTF-8'))
                    if vu.bezae_correctors.has_key('C'):
                        bez_file.write((u'\tC\t' + vu.bezae_correctors['C'] + u'\n').encode('UTF-8'))
                    if vu.bezae_correctors.has_key('D'):
                        bez_file.write((u'\tD\t' + vu.bezae_correctors['D'] + u'\n').encode('UTF-8'))
                    if vu.bezae_correctors.has_key('E'):
                        bez_file.write((u'\tE\t' + vu.bezae_correctors['E'] + u'\n').encode('UTF-8'))
                    if vu.bezae_correctors.has_key('H'):
                        bez_file.write((u'\tH\t' + vu.bezae_correctors['H'] + u'\n').encode('UTF-8'))
                    bez_file.write(u'\n')

                    bez_file.write(u'sort_id\treading_id\treading_text\tsm\tA\tB\tC\tD\tE\tH\t05\t35')
                    for ms in greekMSS:
                        if ms != '05' and ms != '35':
                            bez_file.write(u'\t' + ms)
                    for ms in latinMSS:
                        bez_file.write(u'\t' + ms)
                    bez_file.write(u'\n')

                    for idx, reading in enumerate(vu.readings):
                        if not reading.manuscripts:
                            continue

                        reading_id = vu.label + letters[idx + 1]
                        sort_id = s.generateSortLabel(vu.label) + letters[idx + 1]
                        reading_text = reading.getDisplayValue()
                        is05sm = False
                        if vu.bezae_correctors.has_key('sm') and reading_text == vu.bezae_correctors['sm']:
                            is05sm = True
                        is05A = False
                        if vu.bezae_correctors.has_key('A') and reading_text == vu.bezae_correctors['A']:
                            is05A = True
                        is05B = False
                        if vu.bezae_correctors.has_key('B') and reading_text == vu.bezae_correctors['B']:
                            is05B = True
                        is05C = False
                        if vu.bezae_correctors.has_key('C') and reading_text == vu.bezae_correctors['C']:
                            is05C = True
                        is05D = False
                        if vu.bezae_correctors.has_key('D') and reading_text == vu.bezae_correctors['D']:
                            is05D = True
                        is05E = False
                        if vu.bezae_correctors.has_key('E') and reading_text == vu.bezae_correctors['E']:
                            is05E = True
                        is05H = False
                        if vu.bezae_correctors.has_key('H') and reading_text == vu.bezae_correctors['H']:
                            is05H = True

                        bez_file.write((sort_id + u'\t' + reading_id + u'\t' + reading_text + u'\t').encode('UTF-8'))
                        if is05sm:
                            bez_file.write((u'1').encode('UTF-8'))
                        bez_file.write((u'\t').encode('UTF-8'))
                        if is05A:
                            bez_file.write((u'1').encode('UTF-8'))
                        bez_file.write((u'\t').encode('UTF-8'))
                        if is05B:
                            bez_file.write((u'1').encode('UTF-8'))
                        bez_file.write((u'\t').encode('UTF-8'))
                        if is05C:
                            bez_file.write((u'1').encode('UTF-8'))
                        bez_file.write((u'\t').encode('UTF-8'))
                        if is05D:
                            bez_file.write((u'1').encode('UTF-8'))
                        bez_file.write((u'\t').encode('UTF-8'))
                        if is05E:
                            bez_file.write((u'1').encode('UTF-8'))
                        bez_file.write((u'\t').encode('UTF-8'))
                        if is05H:
                            bez_file.write((u'1').encode('UTF-8'))
                        bez_file.write((u'\t').encode('UTF-8'))
                        bez_file.write((s.getMSValue(vu, reading, '05') + u'\t' + s.getMSValue(vu, reading, '35')).encode('UTF-8'))

                        for ms in greekMSS:
                            if ms != '05' and ms != '35':
                                bez_file.write(u'\t' + s.getMSValue(vu, reading, ms))
                        for ms in latinMSS:
                            bez_file.write(u'\t' + s.getMSValue(vu, reading, ms))
                        bez_file.write(u'\n')

                    bez_file.write(u'\n')

        bez_file.close()
        sai_file.close()

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

    def generateVariationHeader(s):
        c = s.config
        s.info('Generating variation header')

        ranges = c.get('rangeData')[s.range_id]
        if not ranges:
            raise ValueError('Please specify one range (chapter).')
        elif len(ranges) > 1:
            raise ValueError('Variation header currently supports ranges consisting of just one chapter.')
        chapter = ranges[0]['chapter']
        cur_v = ranges[0]['startVerse']

        SEP = u'\t'
        lines = ['', '', '']
        lines[0] = str(cur_v).decode('utf-8') + SEP
        lines[1] = str(cur_v).decode('utf-8') + SEP
        lines[2] = str(cur_v).decode('utf-8') + SEP
        for addr in s.variantModel['addresses']:
            while cur_v < addr.verse_num:
                cur_v = cur_v + 1
                lines[0] = lines[0] + str(cur_v).decode('utf-8') + SEP
                lines[1] = lines[1] + str(cur_v).decode('utf-8') + SEP
                lines[2] = lines[2] + str(cur_v).decode('utf-8') + SEP

            for vidx, vu in enumerate(addr.variation_units):
                if not vu.startingAddress:
                    vu.startingAddress = addr

                r_reading = vu.getReadingForManuscript(s.refMS)
                r_layer = s.computeLayer2(s.refMS, vu, r_reading)

                output = r_layer + vu.label
                if r_layer[:1] == 'S' or vu.isSingular():
                    output = '*' + output
                if r_reading:
                    output = output + ' ' + readingsToString(vu, r_reading)
                else:
                    output = output + ' '

                lines[vidx] = lines[vidx] + output + SEP

            for i in range(len(addr.variation_units), 3):
                lines[i] = lines[i] + SEP

        csvFile = c.get('finderFolder') + '/' + s.refMS + '-varheader-' + s.range_id + '.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write((lines[0] + u'\n').encode('utf-8'))
            csv_file.write((lines[1] + u'\n').encode('utf-8'))
            csv_file.write((lines[2] + u'\n').encode('utf-8'))
            csv_file.close()

    def generateLayerApparatus(s, layer):
        c = s.config
        s.info('Generating layer apparatus')

        msGroupAssignments = c.get('msGroupAssignments')
        apparatusLabels = c.get('apparatusLabels') # if present, layer is ignored
        if apparatusLabels:
            apparatusLabels = apparatusLabels.split('|')

        csvFile = c.get('finderFolder') + '/' + s.refMS + '-apparatus-' + layer + '.csv'
        with open(csvFile, 'w+') as csv_file:
            csv_file.write('Reference\tReadings\tReading Count\tMSS\tLayer\tApparatus\n')
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

                    if r_layer != 'S':
                        r_layer = s.computeLayer(vu.label, r_reading, False)

                    if apparatusLabels and not vu.label in apparatusLabels:
                        continue
                    elif not apparatusLabels and r_layer != layer:
                        continue

                    r_mss = ''
                    if apparatusLabels:
                        r_mss = mssGroupListToString(r_reading.manuscripts, msGroupAssignments, None, None)
                    else:
                        r_mss = mssListToString(r_reading.manuscripts)

                    all_readings = ''
                    all_readings = all_readings + r_reading.getDisplayValue()
                    for reading in vu.readings:
                        if reading == r_reading:
                            continue

                        if len(all_readings) > 0:
                            all_readings = all_readings + ' | '
                        all_readings = all_readings + reading.getDisplayValue()

                    csv_file.write((vu.label + u'\t' + all_readings + u'\t' + str(len(vu.readings)) + u'\t' + r_mss + u'\t' + r_layer + u'\t' + vu.toApparatusString() + u'\n').encode('UTF-8'))

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
            for label in s.latinLayerCore:
                if not all_labels.has_key(label):
                    csv_file.write((label + u'\n').encode('UTF-8'))
            for label in s.latinLayerMulti:
                if not all_labels.has_key(label):
                    csv_file.write((label + u'\n').encode('UTF-8'))

            csv_file.close()

    def refNonMainstream(s):
        c = s.config

        file = open(c.get('finderFolder') + '/' + s.refMS + '-nonmainstream.csv', 'w+')
        file.write(('Sort ID\tLabel\tReading\tSupport\tAll Readings\n').encode('UTF-8'))
        for addr in s.variantModel['addresses']:
            for vu in addr.variation_units:
                if not vu.startingAddress:
                    vu.startingAddress = addr

                if vu.isReferenceSingular(s.refMS):
                    continue

                reading = vu.getReadingForManuscript(s.refMS)
                if not reading:
                    continue

                if reading.hasManuscript('35'):
                    continue

                file.write((s.generateSortLabel(vu.label) + u'\t').encode('UTF-8'))
                file.write((vu.label + u'\t').encode('UTF-8'))
                file.write((reading.getDisplayValue() + u'\t').encode('UTF-8'))

                mss_str = ''
                for ms in reading.manuscripts:
                    if mss_str:
                        mss_str = mss_str + ' '
                    mss_str = mss_str + ms

                file.write((mss_str + u'\t').encode('UTF-8'))

                all_readings = ''
                all_readings = all_readings + reading.getDisplayValue()
                for rdg in vu.readings:
                    if reading == rdg:
                        continue

                    if len(all_readings) > 0:
                        all_readings = all_readings + ' | '
                    all_readings = all_readings + rdg.getDisplayValue()

                file.write((all_readings + u'\n').encode('UTF-8'))

        file.close()

    def refSingulars(s):
        c = s.config

        msGroupAssignments = c.get('msGroupAssignments')

        file = open(c.get('finderFolder') + '/' + s.refMS + '-singulars.csv', 'w+')
        file.write(('Sort ID\tLabel\tReading\tSupport\tMainstream Reading\tAll Readings\n').encode('UTF-8'))
        for addr in s.variantModel['addresses']:
            for vu in addr.variation_units:
                if not vu.startingAddress:
                    vu.startingAddress = addr

                reading = vu.getReadingForManuscript(s.refMS)
                if not reading:
                    continue

                mainstream_reading = vu.getReadingForManuscript('35')

                g_counts = {}
                g_count = reading.countNonRefGreekManuscriptsByGroup(s.refMS, msGroupAssignments, g_counts)
                if vu.isReferenceSingular(s.refMS):
                    file.write((s.generateSortLabel(vu.label) + u'\t').encode('UTF-8'))
                    file.write((vu.label + u'\t').encode('UTF-8'))
                    file.write((reading.getDisplayValue() + u'\t\t').encode('UTF-8'))
                elif g_count <= 1:
                    file.write((s.generateSortLabel(vu.label) + u'\t').encode('UTF-8'))
                    file.write((vu.label + u'\t').encode('UTF-8'))
                    file.write((reading.getDisplayValue() + u'\t').encode('UTF-8'))

                    mss_str = ''
                    for ms in reading.manuscripts:
                        if mss_str:
                            mss_str = mss_str + ' '
                        mss_str = mss_str + ms

                    file.write((mss_str + u'\t').encode('UTF-8'))
                else:
                    continue

                file.write((mainstream_reading.getDisplayValue() + u'\t').encode('UTF-8'))

                all_readings = ''
                all_readings = all_readings + reading.getDisplayValue()
                all_readings = all_readings + '|' + mainstream_reading.getDisplayValue()
                for rdg in vu.readings:
                    if reading == rdg or mainstream_reading == rdg:
                        continue

                    if len(all_readings) > 0:
                        all_readings = all_readings + ' | '
                    all_readings = all_readings + rdg.getDisplayValue()

                file.write((all_readings + u'\n').encode('UTF-8'))

        file.close()
                    
    def fixHarmLayers(s):
        c = s.config

        layer_map = {}
        for addr in s.variantModel['addresses']:
            for vu in addr.variation_units:
                if not vu.startingAddress:
                    vu.startingAddress = addr

                r_layer = ''
                is_singular = False
                if vu.isReferenceSingular(s.refMS):
                    is_singular = True
                    r_layer = 'S'
                elif vu.isSingular():
                    is_singular = True
                    r_layer = '*'

                if s.refMS == '05' and isSubSingular(s.config.get('subsingularVariants'), vu, s.refMS):
                    is_singular = True
                    r_layer = 'SS'

                r_reading = vu.getReadingForManuscript(s.refMS)
                if not r_reading:
                    r_layer = 'N'

                if not r_layer:
                    r_layer = s.computeLayer(vu.label, r_reading, True)

                layer_map[vu.label] = r_layer

        harm_file = c.get('inputFolder') + 'harm-fix.csv'
        csvdata = ''
        with open(harm_file, 'r') as file:
            s.info('reading', harm_file)
            csvdata = file.read().decode('utf-8')
            file.close()

        result_file = c.get('outputFolder') + 'harm-fix-results.csv'
        with open(result_file, 'w+') as file:
            rows = csvdata.split('\n')
            for rdx, row in enumerate(rows):
                parts = row.split('\t')
                if len(parts) != 2:
                    continue

                label = parts[0]
                lookup = re.sub(r'[a-z]$', '', label)

                layer = ''
                if layer_map.has_key(lookup):
                    layer = layer_map[lookup]

                file.write(label + '\t' + layer + '\n')

            file.close()

    def initRadius(s):
        r_dat = {}
        r_dat['density_profile'] = []
        r_dat['max'] = 0
        r_dat['mean'] = 0
        r_dat['min'] = 1000
        r_dat['sum'] = 0
        return r_dat

    def initLayer(s):
        l_dat = {}
        l_dat['labels'] = []
        l_dat['p_set'] = set()
        l_dat['points'] = []
        return l_dat

    def initLayerData(s, l_map, label, word_index):
        l_map['labels'].append(label)
        l_map['p_set'].add(word_index)
        l_map['points'].append(word_index)

    def computeAgglom(s, density_map, percentile, is_gaps):
        agglom_data = {}
        agglom_data['spans'] = []
        agglom_data['min_span'] = 1000
        agglom_data['max_span'] = 0

        is_agglom = False
        span_counter = 0
        val = np.percentile(density_map, percentile)
        for density in density_map:
            if not is_gaps and density >= val:
                is_agglom = True
                span_counter = span_counter + 1
            elif is_gaps and density <= val:
                is_agglom = True
                span_counter = span_counter + 1
            else:
                if is_agglom:
                    agglom_data['spans'].append(span_counter)
                    if span_counter < agglom_data['min_span']:
                        agglom_data['min_span'] = span_counter
                    if span_counter > agglom_data['max_span']:
                        agglom_data['max_span'] = span_counter
                span_counter = 0
                is_agglom = False
        if is_agglom: # last time
            agglom_data['spans'].append(span_counter)
            if span_counter < agglom_data['min_span']:
                agglom_data['min_span'] = span_counter
            if span_counter > agglom_data['max_span']:
                agglom_data['max_span'] = span_counter

        agglom_data['count'] = len(agglom_data['spans'])
        agglom_data['mean_span'] = round(np.mean(agglom_data['spans']), 3)
        agglom_data['median_span'] = np.percentile(agglom_data['spans'], 50)

        return agglom_data

    def printStat(s, file, LAYERS, RADII, l_map, label, stat_key):
        for layer in LAYERS:
            file.write(label)
            for r in RADII:
                file.write('\t' + str(l_map[layer][r][stat_key]))
            file.write('\t\t')
        file.write('\n')

    def printPercentile(s, file, LAYERS, RADII, l_map, label, percentile):
        for layer in LAYERS:
            file.write(label)
            for r in RADII:
                file.write('\t' + str(np.percentile(l_map[layer][r]['density_profile'], percentile)))
            file.write('\t\t')
        file.write('\n')

    def printAgglom(s, file, LAYERS, RADII, l_map, label, percentile, ag_key, is_gaps):
        for layer in LAYERS:
            file.write(label)
            for r in RADII:
                ag = s.computeAgglom(l_map[layer][r]['density_profile'], percentile, is_gaps)
                file.write('\t' + str(ag[ag_key]))
            file.write('\t\t')
        file.write('\n')

    def writeDensity(s, LAYERS, RADII, l_map, INTERVAL, interval_points, is_interval, is_normalized):
        c = s.config

        extra_str = ''
        if is_interval:
            extra_str = '-interval'
        if is_normalized:
            extra_str = extra_str + '-norm'
        file = open(c.get('finderFolder') + 'layer_density' + extra_str + '.csv', 'w+')
        for layer in LAYERS:
            file.write(layer + ' Layer')
            for r in RADII:
                file.write('\t' + str(r))
            file.write('\t\t')
        file.write('\n') # header

        for layer in LAYERS:
            file.write('Readings:')
            for r in RADII:
                file.write('\t' + str(len(l_map[layer]['points'])))
            file.write('\t\t')
        file.write('\n')

        s.printStat(file, LAYERS, RADII, l_map, 'Mean:', 'mean')

        for layer in LAYERS:
            file.write('STD:')
            for r in RADII:
                file.write('\t' + str(round(np.std(l_map[layer][r]['density_profile']), 3)))
            file.write('\t\t')
        file.write('\n')

        for layer in LAYERS:
            file.write('Coef Var:')
            for r in RADII:
                file.write('\t' + str(round(np.std(l_map[layer][r]['density_profile']) / l_map[layer][r]['mean'], 3)))
            file.write('\t\t')
        file.write('\n')

        s.printStat(file, LAYERS, RADII, l_map, 'Min:', 'min')
        s.printStat(file, LAYERS, RADII, l_map, 'Max:', 'max')
        
        for layer in LAYERS:
            file.write('Median:')
            for r in RADII:
                file.write('\t' + str(np.percentile(l_map[layer][r]['density_profile'], 50)))
            file.write('\t\t')
        file.write('\n')

        for layer in LAYERS:
            file.write('Skew:')
            for r in RADII:
                file.write('\t' + str(round(stats.skew(l_map[layer][r]['density_profile']), 3)))
            file.write('\t\t')
        file.write('\n')

        for layer in LAYERS:
            file.write('Kurtosis:')
            for r in RADII:
                file.write('\t' + str(round(stats.kurtosis(l_map[layer][r]['density_profile']), 3)))
            file.write('\t\t')
        file.write('\n')

        s.printPercentile(file, LAYERS, RADII, l_map, '5 Percentile:', 5)
        s.printAgglom(file, LAYERS, RADII, l_map, '5% Agglomerations:', 5, 'count', True)
        s.printAgglom(file, LAYERS, RADII, l_map, '5% Ag Mean Span:', 5, 'mean_span', True)
        s.printAgglom(file, LAYERS, RADII, l_map, '5% Ag Max Span:', 5, 'max_span', True)
        s.printAgglom(file, LAYERS, RADII, l_map, '5% Ag Min Span:', 5, 'min_span', True)
        s.printAgglom(file, LAYERS, RADII, l_map, '5% Ag Median Span:', 5, 'median_span', True)

        s.printPercentile(file, LAYERS, RADII, l_map, '10 Percentile:', 10)
        s.printAgglom(file, LAYERS, RADII, l_map, '10% Agglomerations:', 10, 'count', True)
        s.printAgglom(file, LAYERS, RADII, l_map, '10% Ag Mean Span:', 10, 'mean_span', True)
        s.printAgglom(file, LAYERS, RADII, l_map, '10% Ag Max Span:', 10, 'max_span', True)
        s.printAgglom(file, LAYERS, RADII, l_map, '10% Ag Min Span:', 10, 'min_span', True)
        s.printAgglom(file, LAYERS, RADII, l_map, '10% Ag Median Span:', 10, 'median_span', True)

        s.printPercentile(file, LAYERS, RADII, l_map, '95 Percentile:', 95)
        s.printAgglom(file, LAYERS, RADII, l_map, '95% Agglomerations:', 95, 'count', False)
        s.printAgglom(file, LAYERS, RADII, l_map, '95% Ag Mean Span:', 95, 'mean_span', False)
        s.printAgglom(file, LAYERS, RADII, l_map, '95% Ag Max Span:', 95, 'max_span', False)
        s.printAgglom(file, LAYERS, RADII, l_map, '95% Ag Min Span:', 95, 'min_span', False)
        s.printAgglom(file, LAYERS, RADII, l_map, '95% Ag Median Span:', 95, 'median_span', False)

        s.printPercentile(file, LAYERS, RADII, l_map, '90 Percentile:', 90)
        s.printAgglom(file, LAYERS, RADII, l_map, '90% Agglomerations:', 90, 'count', False)
        s.printAgglom(file, LAYERS, RADII, l_map, '90% Ag Mean Span:', 90, 'mean_span', False)
        s.printAgglom(file, LAYERS, RADII, l_map, '90% Ag Max Span:', 90, 'max_span', False)
        s.printAgglom(file, LAYERS, RADII, l_map, '90% Ag Min Span:', 90, 'min_span', False)
        s.printAgglom(file, LAYERS, RADII, l_map, '90% Ag Median Span:', 90, 'median_span', False)

        file.write('\n')

        row_count = len(interval_points)
        if not is_interval:
            for layer in LAYERS:
                if len(l_map[layer]['points']) > row_count:
                    row_count = len(l_map[layer]['points'])

        for idx in range(0, row_count):
            for layer in LAYERS:
                limit = len(l_map[layer]['labels'])
                if is_interval:
                    limit = len(interval_points)
                if idx >= limit:
                    for r in RADII:
                        file.write('\t')
                    file.write('\t\t')
                    continue

                label = str(idx + 1)
                if not is_interval:
                    label = l_map[layer]['labels'][idx]
                else:
                    label_key = str((idx + 1) * INTERVAL)
                    label = s.rangeMgr.word_map_05[label_key] if s.rangeMgr.word_map_05.has_key(label_key) else ''
                    if label:
                        label = label + ' '
                    label = label + '(' + str(idx + 1) + ')'
                file.write(label)
                for r in RADII:
                    file.write('\t' + str(l_map[layer][r]['density_profile'][idx]))
                file.write('\t\t')
            file.write('\n')

        file.close()

    def computeDensity(s, is_interval):
        c = s.config
        s.info('Computing density')

        INTERVAL = 15
        LAYERS = [ 'L', '01C1', 'F03', 'C565', '01A', '05A', '05B', 'G', 'M', 'VL5' ]
        MAX_WORD_INDEX = 11435
        RADII = [ 30, 60, 90, 120, 150, 180 ]
        REF_MS = '05'

        interval_points = list(range(INTERVAL, MAX_WORD_INDEX - INTERVAL, INTERVAL))

        l_map = {}
        for layer in LAYERS:
            l_map[layer] = s.initLayer()
            for r in RADII:
                l_map[layer][r] = s.initRadius()

        for aidx, addr in enumerate(s.variantModel['addresses']):
            for vu in addr.variation_units:

                if not vu.startingAddress:
                    vu.startingAddress = addr

                reading = vu.getReadingForManuscript(REF_MS)
                if reading:
                    layer = s.computeLayer2(REF_MS, vu, reading)
                    if layer == 'L' or layer == 'LI':
                        s.initLayerData(l_map['L'], vu.label, vu.word_index_05)

                if vu.getReadingForCorrector('01C1'):
                    s.initLayerData(l_map['01C1'], vu.label, vu.word_index_05)

                for group in c.get('coreGroups'):
                    if group['name'] != 'F03' and group['name'] != 'C565': continue
                    if isDistinctive(c.get('msGroupAssignments'), REF_MS, vu, reading, group):
                        s.initLayerData(l_map[group['name']], vu.label, vu.word_index_05)

                if vu.getReadingForCorrector('01A'):
                    s.initLayerData(l_map['01A'], vu.label, vu.word_index_05)

                if vu.getReadingForCorrector('05A'):
                    s.initLayerData(l_map['05A'], vu.label, vu.word_index_05)

                if vu.getReadingForCorrector('05B'):
                    s.initLayerData(l_map['05B'], vu.label, vu.word_index_05)

                if reading and layer == 'M':
                    s.initLayerData(l_map['M'], vu.label, vu.word_index_05)
                elif reading and (layer[:1] == 'B' or layer[:1] == 'C' or layer[:1] == 'G' or layer[:1] == 'W'):
                    s.initLayerData(l_map['G'], vu.label, vu.word_index_05)

                vl5_reading = vu.getReadingForManuscript('VL5')
                if vl5_reading and not vu.isSingular():
                    if not vl5_reading.hasManuscript('35') and not vl5_reading.hasManuscript('05'):
                        s.initLayerData(l_map['VL5'], vu.label, vu.word_index_05)

        for layer in LAYERS:
            all_points = l_map[layer]['points']
            if is_interval:
                all_points = interval_points
    
            for word_idx in all_points:
                for r in RADII:
                    radius_points = set(range(word_idx - r, word_idx + r + 1))
                    density = len(radius_points & l_map[layer]['p_set'])

                    # Scale density for missing edge values
                    if word_idx - r < 0: # bottom
                        short_range = 2 * r - abs(word_idx - r)
                        density = 2 * r * density / short_range
                    if word_idx + r > MAX_WORD_INDEX: # top
                        short_range = 2 * r - (word_idx + r - MAX_WORD_INDEX)
                        density = 2 * r * density / short_range

                    if density > l_map[layer][r]['max']:
                        l_map[layer][r]['max'] = density
                    elif density < l_map[layer][r]['min']:
                        l_map[layer][r]['min'] = density
                    l_map[layer][r]['sum'] = l_map[layer][r]['sum'] + density
                    l_map[layer][r]['density_profile'].append(density)

        for layer in LAYERS:
            num_points = len(l_map[layer]['points']) if not is_interval else len(interval_points)
            for r in RADII:
                l_map[layer][r]['mean'] = round(l_map[layer][r]['sum'] * 1.0 / num_points, 3) if num_points > 0 else 0.0

        s.writeDensity(LAYERS, RADII, l_map, INTERVAL, interval_points, is_interval, False)

        for layer in LAYERS:
            for r in RADII:
                old_min = l_map[layer][r]['min']

                sum = 0
                l_map[layer][r]['min'] = 0
                scaled_max = l_map[layer][r]['max'] - old_min
                for idx, density in enumerate(l_map[layer][r]['density_profile']):
                    density = round((density - old_min) * 20.0 / scaled_max, 3)
                    l_map[layer][r]['density_profile'][idx] = density
                    sum = sum + density
                l_map[layer][r]['sum'] = sum
                l_map[layer][r]['max'] = 20
                l_map[layer][r]['mean'] = round(sum * 1.0 / num_points, 3) if num_points > 0 else 0.0

        s.writeDensity(LAYERS, RADII, l_map, INTERVAL, interval_points, is_interval, True)

    def bezanLatinAgreements(s):
        c = s.config
        s.info('Computing Bezan Latin agreements')

        latin_mss = [ '05' ]
        latin_mss.extend(c.get('latinMSS'))

        bz_lyrs = ['C', 'CC', 'CB', 'CW', 'CCC', 'B', 'BB', 'W', 'WW', 'G', 'GG', 'M', 'LATIN', 'NONLATIN_NONMAJORITY', 'VL5_NONMAJORITY']
        italian_mss = [ 'VL4', 'VL8', 'VL13', 'VL14', 'VL17' ]

        all_layers = {}
        for lyr in bz_lyrs:
            layer_stats = {}
            layer_stats['stats'] = {}
            layer_stats['attested_counts'] = {}
            for ms in latin_mss:
                layer_stats['stats'][ms] = []
                layer_stats['attested_counts'][ms] = 0
            layer_stats['ital_stats'] = []
            all_layers[lyr] = layer_stats

        ref_ms = 'VL5'
        for addr in s.variantModel['addresses']:
            for vidx, vu in enumerate(addr.variation_units):
                if not vu.startingAddress:
                    vu.startingAddress = addr

                if vu.isSingular() or vu.isReferenceSingular(ref_ms):
                    continue

                r_reading = vu.getReadingForManuscript(ref_ms)
                if not r_reading:
                    continue

                if r_reading.hasManuscript('35'):
                    continue

                b_reading = vu.getReadingForManuscript('05')
                m_reading = vu.getReadingForManuscript('35')

                all_readings = ''
                all_readings = all_readings + r_reading.getDisplayValue() + ' | ' + m_reading.getDisplayValue()
                for reading in vu.readings:
                    if reading == r_reading or reading == m_reading:
                        continue

                    if len(all_readings) > 0:
                        all_readings = all_readings + ' | '
                    all_readings = all_readings + reading.getDisplayValue()

                r_info = {}
                r_info['verse'] = vu.label
                r_info['all_readings'] = all_readings
                r_info['mss'] = r_reading.manuscripts
                r_info['apparatus'] = vu.toApparatusString()
                r_info['has_05'] = True if '05' in r_reading.manuscripts else False
                r_info['reading_05'] = b_reading.getDisplayValue() if b_reading else ''
                r_info['reading_35'] = m_reading.getDisplayValue()
                r_info['reading_VL5'] = r_reading.getDisplayValue()
                r_info['word_index'] = vu.word_index_05

                extant_mss = vu.getExtantManuscripts()
                for ms in latin_mss:
                    if ms in extant_mss:
                        all_layers['VL5_NONMAJORITY']['attested_counts'][ms] = all_layers['VL5_NONMAJORITY']['attested_counts'][ms] + 1

                for ms in r_reading.manuscripts:
                    if ms in latin_mss:
                        all_layers['VL5_NONMAJORITY']['stats'][ms].append(r_info)

                if set(italian_mss) & set(r_reading.manuscripts):
                    all_layers['VL5_NONMAJORITY']['ital_stats'].append(r_info)

                if not b_reading:
                    continue

                layer = s.computeLayer3('05', vu, b_reading)
                if layer[:1] == 'L':
                    layer = 'LATIN'

                if layer != 'LATIN' and layer != 'M':
                    for ms in latin_mss:
                        if ms in extant_mss:
                            all_layers['NONLATIN_NONMAJORITY']['attested_counts'][ms] = all_layers['NONLATIN_NONMAJORITY']['attested_counts'][ms] + 1

                    for ms in r_reading.manuscripts:
                        if ms in latin_mss:
                            all_layers['NONLATIN_NONMAJORITY']['stats'][ms].append(r_info)

                    if set(italian_mss) & set(r_reading.manuscripts):
                        all_layers['NONLATIN_NONMAJORITY']['ital_stats'].append(r_info)

                if layer in bz_lyrs:
                    if layer == 'NONLATIN_NONMAJORITY' or layer == 'VL5_NONMAJORITY':
                        continue

                    for ms in latin_mss:
                        if ms in extant_mss:
                            all_layers[layer]['attested_counts'][ms] = all_layers[layer]['attested_counts'][ms] + 1

                    for ms in r_reading.manuscripts:
                        if ms in latin_mss:
                            all_layers[layer]['stats'][ms].append(r_info)

                    if set(italian_mss) & set(r_reading.manuscripts):
                        all_layers[layer]['ital_stats'].append(r_info)

        file = open(c.get('finderFolder') + '/bezan-latin-agreements-summary.csv', 'w+')
        file.write('MS\tAgreements\tAttested\tRatio\tPercent\n')
        for lyr in bz_lyrs:
            file.write(lyr + '\n')
            for ms in latin_mss:
                agreements = len(all_layers[lyr]['stats'][ms])
                attested_counts = all_layers[lyr]['attested_counts']
                percent = round(agreements * 1.0 / attested_counts[ms], 3) if attested_counts[ms] > 0 else 0.0
                file.write(ms + '\t' + str(agreements) + '\t' + str(attested_counts[ms]) + '\t' + str(agreements) + '/' + str(attested_counts[ms]) + '\t' + str(percent) + '\n')

            agreements = len(all_layers[lyr]['ital_stats'])
            percent = round(agreements * 1.0 / attested_counts['VL5'], 3) if attested_counts['VL5'] > 0 else 0.0
            file.write('Ital\t' + str(agreements) + '\t' + str(attested_counts['VL5']) + '\t' + str(agreements) + '/' + str(attested_counts['VL5']) + '\t' + str(percent) + '\n\n')

        file.close()

        file = open(c.get('finderFolder') + '/bezan-col-diffs.csv', 'w+')
        file.write('Sort ID\tWord Index\tHas 05\tVerse\tVL5 Reading\t05 Reading\tMainstream\tReadings\tMSS\tApparatus\n')
        for info in all_layers['VL5_NONMAJORITY']['stats']['VL5']:
            has_05 = 'Y' if info['has_05'] else 'N'
            file.write((s.generateSortLabel(info['verse']) + u'\t' + str(info['word_index']) + u'\t' + has_05 + u'\t' + info['verse'] + u'\t' + info['reading_VL5'] + u'\t' + info['reading_05'] + u'\t' + info['reading_35'] + u'\t' + info['all_readings'] + u'\t' + mssListToString(info['mss']) + u'\t' + info['apparatus'] + u'\n').encode('UTF-8'))
        file.close()

    def alexAgreements(s):
        c = s.config
        s.info('Computing Alex agreements')

        alex_mss = [ 'P88', '01', '03', '04', '019', '037', '044', '083', '0274', '33', '579', '892', '1342' ]
        core_mss = [ '01', '019', '044' ]

        stats = {}
        attested_counts = {}
        for ms in alex_mss:
            stats[ms] = []
            attested_counts[ms] = 0
        core_stats = []

        ref_ms = '03'
        for addr in s.variantModel['addresses']:
            for vidx, vu in enumerate(addr.variation_units):
                if not vu.startingAddress:
                    vu.startingAddress = addr

                if vu.isSingular() and not vu.isReferenceSingular(ref_ms):
                    continue

                r_reading = vu.getReadingForManuscript(ref_ms)
                if not r_reading:
                    continue

                if r_reading.hasManuscript('35'):
                    continue

                extant_mss = vu.getExtantManuscripts()
                for ms in alex_mss:
                    if ms in extant_mss:
                        attested_counts[ms] = attested_counts[ms] + 1

                r_info = {}
                r_info['verse'] = vu.label

                for ms in r_reading.manuscripts:
                    if ms in alex_mss:
                        stats[ms].append(r_info)

                if set(core_mss) & set(r_reading.manuscripts):
                    core_stats.append(r_info)

        file = open(c.get('finderFolder') + '/f03-agreements-summary.csv', 'w+')
        file.write('MS\tAgreements\tAttested\tRatio\tPercent\n')
        for ms in alex_mss:
            agreements = len(stats[ms])
            percent = round(agreements * 1.0 / attested_counts[ms], 3) if attested_counts[ms] > 0 else 0.0
            file.write(ms + '\t' + str(agreements) + '\t' + str(attested_counts[ms]) + '\t' + str(agreements) + '/' + str(attested_counts[ms]) + '\t' + str(percent) + '\n')

        agreements = len(core_stats)
        percent = round(agreements * 1.0 / attested_counts['03'], 3) if attested_counts['03'] > 0 else 0.0
        file.write('Core\t' + str(agreements) + '\t' + str(attested_counts['03']) + '\t' + str(agreements) + '/' + str(attested_counts['03']) + '\t' + str(percent) + '\n')

        file.close()

    def bobbiensisReadings(s):
        c = s.config
        s.info('Finding vercellensis readings')

        file = open(c.get('finderFolder') + '/vercellensis.csv', 'w+')
        file.write('Verse\tReadings\tMSS\tIs Singular\tHas 03\tHas Distinctive 03\tHas 565\tHas Distinctive 565\tHas 05\tOnly VL\tOnly VL(1 3)\tApparatus\n')

        ref_ms = 'VL3'
        for addr in s.variantModel['addresses']:
            for vidx, vu in enumerate(addr.variation_units):
                if not vu.startingAddress:
                    vu.startingAddress = addr

                if vu.isSingular() and not vu.isReferenceSingular(ref_ms):
                    continue

                r_reading = vu.getReadingForManuscript(ref_ms)
                if not r_reading:
                    continue

                if r_reading.hasManuscript('35'):
                    continue

                m_reading = vu.getReadingForManuscript('35')

                all_readings = ''
                all_readings = all_readings + r_reading.getDisplayValue() + ' | ' + m_reading.getDisplayValue()
                for reading in vu.readings:
                    if reading == r_reading or reading == m_reading:
                        continue

                    if len(all_readings) > 0:
                        all_readings = all_readings + ' | '
                    all_readings = all_readings + reading.getDisplayValue()

                is_singular = ''
                if len(r_reading.manuscripts) == 1:
                    is_singular = 'Y'

                has_03 = ''
                if '03' in r_reading.manuscripts:
                    has_03 = 'Y'

                has_distinctive_03 = ''
                if has_03 and len(r_reading.manuscripts) < 10:
                    has_distinctive_03 = 'Y'

                has_565 = ''
                if '565' in r_reading.manuscripts or '038' in r_reading.manuscripts:
                    has_565 = 'Y'

                has_distinctive_565 = ''
                if has_565 and len(r_reading.manuscripts) < 10:
                    has_distinctive_565 = 'Y'

                has_05 = ''
                if '05' in r_reading.manuscripts:
                    has_05 = 'Y'

                only_vl = 'Y'
                for ms in r_reading.manuscripts:
                    if ms[:2] != 'VL' and ms != '19A' and ms != 'vg':
                        only_vl = ''
                        break

                vl1_and_vl3 = ''
                bob_reading = vu.getReadingForManuscript('VL1')
                if bob_reading and bob_reading != r_reading:
                    vl1_and_vl3 = 'Y'
                    for ms in bob_reading.manuscripts:
                        if ms[:2] != 'VL' and ms != '19A' and ms != 'vg':
                            vl1_and_vl3 = ''
                            break

                file.write((vu.label + u'\t' + all_readings + u'\t' + mssListToString(r_reading.manuscripts) + u'\t' + is_singular + u'\t' + has_03 + u'\t' + has_distinctive_03 + u'\t' + has_565 + u'\t' + has_distinctive_565 + u'\t' + has_05 + u'\t' + only_vl + u'\t' + vl1_and_vl3 + u'\t' + vu.toApparatusString() + u'\n').encode('UTF-8'))

        file.close()

    def analyzeGroups(s):
        c = s.config
        s.info('Analyzing groups')

        groups = { 'F03': [], 'C565': [], '032': [], 'F1': [], 'F13': [], 'P45': [] }
        f03 = set([ "03", "01", "019" ])
        f1 = set([ "1", "1582"])
        f13 = set([ "13", "346", "543", "788", "826", "828", "983"])
        c565 = set([ "038", "565"])

        count = 0
        for addr in s.variantModel['addresses']:
            for vidx, vu in enumerate(addr.variation_units):
                if not vu.startingAddress:
                    vu.startingAddress = addr

                # exclude singulars
                if vu.isSingular() or vu.isReferenceSingular('05'):
                    continue

                latinLayerCore = c.get('latinLayerCoreVariants').split(u'|')
                latinLayerMulti = c.get('latinLayerMultiVariants').split(u'|')
                if vu.label in latinLayerCore or vu.label in latinLayerMulti:
                    continue

                reading = vu.getReadingForManuscript('05')
                if not reading or reading.hasManuscript('35'):
                    continue

                mss = set(reading.manuscripts)
                if mss & f03:
                    groups['F03'].append(vu.label)

                if mss & f1:
                    groups['F1'].append(vu.label)

                if mss & f13:
                    groups['F13'].append(vu.label)

                if mss & c565:
                    groups['C565'].append(vu.label)

                if '032' in mss:
                    groups['032'].append(vu.label)

                if 'P45' in mss:
                    groups['P45'].append(vu.label)

                count = count + 1

        file_name = c.get('finderFolder') + '/group-analysis-' + s.range_id + '.csv'
        file = open(file_name, 'w+')
        file.write('Group\tReadings\tTotal\tPercentage\n')

        # One set
        glen = len(groups['C565'])
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(groups['F03'])
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('F03\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(groups['F1'])
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('F1\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(groups['F13'])
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('F13\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(groups['032'])
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('032\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        # Two sets
        glen = len(set(groups['C565']) | set(groups['F03']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F03\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(set(groups['C565']) | set(groups['F1']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F1\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(set(groups['C565']) | set(groups['F13']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F13\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(set(groups['C565']) | set(groups['032']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U 032\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        # C565 x F03
        glen = len(set(groups['C565']) & set(groups['F03']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 N F03\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        # Three sets
        glen = len(set(groups['C565']) | set(groups['F03']) | set(groups['F1']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F03 U F1\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(set(groups['C565']) | set(groups['F03']) | set(groups['F13']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F03 U F13\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(set(groups['C565']) | set(groups['F03']) | set(groups['032']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F03 U 032\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        # Four sets
        glen = len(set(groups['C565']) | set(groups['F03']) | set(groups['F1']) | set(groups['F13']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F03 U F1 U F13\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(set(groups['C565']) | set(groups['F03']) | set(groups['F13']) | set(groups['032']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F03 U F13 U 032\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(set(groups['C565']) | set(groups['F03']) | set(groups['F1']) | set(groups['032']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F03 U F1 U 032\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        # Five sets
        glen = len(set(groups['C565']) | set(groups['F03']) | set(groups['F1']) | set(groups['F13']) | set(groups['032']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('C565 U F03 U F1 U F13 U 032\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        # P45 x 032
        glen = len(set(groups['032']) & set(groups['P45']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('P45 N 032\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        # Distinctive
        glen = len(set(groups['C565']) - set(groups['F03']) - set(groups['F1']) - set(groups['F13']) - set(groups['032']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('Only C565\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        glen = len(set(groups['F03']) - set(groups['C565']) - set(groups['F1']) - set(groups['F13']) - set(groups['032']))
        pc = round(glen * 1.0 / count, 3) if count > 0 else 0.0
        file.write('Only F03\t' + str(glen) + '\t' + str(count) + '\t' + str(pc) + '\n')

        file.close()

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        delegate = None
        if o.group:
            delegate = Grouper(o.group)
            delegate.initialize()

        if not delegate or not delegate.isInitialized():
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

            s.latinLayerCore = c.get('latinLayerCoreVariants').split(u'|')
            s.latinLayerMulti = c.get('latinLayerMultiVariants').split(u'|')

            is_refresh = False
            if o.refreshCache:
                is_refresh = True

            # load variant data
            s.rangeMgr = RangeManager()
            s.rangeMgr.load(is_refresh)

            s.variantModel = s.rangeMgr.getModel(s.range_id)

        if s.queryCriteria:
            s.initAddrLookup()
            s.findCriteria()
        elif o.layer:
            s.generateLayerApparatus(o.layer)
            #s.findMissingLatinVariants()
        elif o.group:
            delegate.variantModel = s.variantModel
            delegate.group()
        elif o.corrector:
            s.generateCorrectorTemplate(s.range_id)
        elif o.harmonization:
            s.generateHarmonizationTemplate(s.range_id)
        elif o.varheader:
            s.generateVariationHeader()
        elif o.latinlayer:
            s.buildLatinLayer()
        elif o.nonmajoritylayers:
            s.buildNonMajorityLayers()
        elif o.extra:
            #s.refNonMainstream()
            #s.refSingulars()
            #s.fixHarmLayers()
            #s.bobbiensisReadings()
            #s.bezanLatinAgreements()
            #s.alexAgreements()
            s.analyzeGroups()
        elif o.density:
            s.computeDensity(False)
            s.computeDensity(True)
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
# Generate layer apparatus
# variantFinder.py -v -a c01-16 -R 05 -L L
#
# Generate harmonization template
# variantFinder.py -v -a c13 -R 05 -Z
#
# Generate corrector template
# variantFinder.py -v -a c01 -R 05 -E
#
# Density analysis
# variantFinder.py -v -r -a c01-16 -R 05 -D
#
# Generate variation header for collation
# variantFinder.py -v -a c13 -R 05 -V
#
# Latin-layer builder
# variantFinder.py -v -a c01-16 -R 05 -Y
#
# Non-majority base layers builder
# variantFinder.py -v -a c01-16 -R 05 -N
#
# Reference singulars
# variantFinder.py -v -a c01-16 -R 032 -X
#
# Bobbiensis
# variantFinder.py -v -a c01-16 -R 05 -X
#
# Group MSS
# variantFinder.py -v -a c01-16 -P
# variantFinder.py -v -a c01-16 -P greek
VariantFinder().main(sys.argv[1:])
