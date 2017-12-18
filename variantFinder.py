#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, re

from object.jsonEncoder import *
from object.rangeManager import *

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

    def refListToString(s, ref_list):
        r_str = ''
        r_map = {}
        r_list = []
        for ref in ref_list:
            if not r_map.has_key(ref):
                r_map[ref] = 1
                r_list.append(ref)
            else:
                r_map[ref] = r_map[ref] + 1
        for ref in r_list:
            if r_map.has_key(ref) and r_map[ref] > 1:
                ref = ref + ' (' + str(r_map[ref]) + 'x)'
            if r_str:
                r_str = r_str + '; '
            r_str = r_str + ref
        return r_str

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
                s.info('Non-core reading in latinLayerCoreVariants', label)
            elif label in s.latinLayerMulti:
                s.info('Non-multi reading in latinLayerMultiVariants', label)
        if not vu.hasRetroversion:
            layer = layer + 'NR'
        return layer

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
                                'groupMSS': mssGroupListToString(reading.manuscripts, msGroupAssignments, g_counts),
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
                    v_str = s.refListToString(v_list)
                    csv_file.write(v_str + '\n')

            csv_file.write('\n')
            csv_file.write('Group\tSingular Agreements\tVerses\n')
            for sg_grp in greekGroups:
                if bz_sing_group_agreemts.has_key(sg_grp):
                    v_list = bz_sing_group_agreemts[sg_grp]
                    csv_file.write(sg_grp + '\t' + str(len(v_list)) + '\t')

                    # refListToString
                    v_str = s.refListToString(v_list)
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
        apparatusLabels = c.get('apparatusLabels')
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
                        r_mss = mssGroupListToString(r_reading.manuscripts, msGroupAssignments, None)
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
        elif o.harmonization:
            s.generateHarmonizationTemplate(s.range_id)
        elif o.varheader:
            s.generateVariationHeader()
        elif o.latinlayer:
            s.buildLatinLayer()
        elif o.extra:
            s.fixHarmLayers()
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
# Generate variation header for collation
# variantFinder.py -v -a c13 -R 05 -V
#
# Latin-layer builder
# variantFinder.py -v -a c01-16 -R 05 -Y
VariantFinder().main(sys.argv[1:])
