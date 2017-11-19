#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, re
from object.util import *
from utility.config import *
from utility.options import *

def sortMSCounts(msc1, msc2):
    pc1 = msc1['count'] * 1.0 / msc1['extant'] if msc1['extant'] != 0 else 0
    pc2 = msc2['count'] * 1.0 / msc2['extant'] if msc2['extant'] != 0 else 0
    if pc1 < pc2:
        return 1
    elif pc1 > pc2:
        return -1
    return 0

class HarmAnalyzer:

    NO_MAJ = True

    def __init__(s):
        s.config = None
        s.options = None

        s.refMS_IDs = []
        s.vus = []
        s.results = {}
        s.reading_map = {}

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def harmonizationsByAgreement(s, ms, h_label):
        c = s.config

        ms_results = {}
        for res in s.results['reference_mss']:
            if res['ms'] == ms:
                ms_results = res
                break

        csvFile = c.get('outputFolder') + h_label + '-agreements.csv'
        with open(csvFile, 'w+') as csv_file:
            if not HarmAnalyzer.NO_MAJ:
                csv_file.write('M Layer (' + str(len(ms_results['byz_parallels'])) + ' parallels)\n')
                csv_file.write('Manuscript\tCount\n')
                for msc in ms_results['bz_mss']:
                    csv_file.write(msc['ms'] + '\t' + str(msc['count']) + '/' + str(ms_results['bz_extant'][msc['ms']]) + '\t' + str(round(msc['count'] * 1.0 / ms_results['bz_extant'][msc['ms']], 3) if ms_results['bz_extant'][msc['ms']] else 0) + '\n')
                csv_file.write('\n')

            csv_file.write('G Layer (' + str(len(ms_results['greek_parallels'])) + ' parallels)\n')
            csv_file.write('Manuscript\tCount\n')
            for msc in ms_results['gr_mss']:
                csv_file.write(msc['ms'] + '\t' + str(msc['count']) + '/' + str(ms_results['gr_extant'][msc['ms']]) + '\t' + str(round(msc['count'] * 1.0 / ms_results['gr_extant'][msc['ms']], 3) if ms_results['gr_extant'][msc['ms']] else 0) + '\n')

            csv_file.write('\n')
            csv_file.write('L Layer (' + str(len(ms_results['latin_parallels'])) + ' parallels)\n')
            csv_file.write('Manuscript\tCount\n')
            for msc in ms_results['la_mss']:
                csv_file.write(msc['ms'] + '\t' + str(msc['count']) + '/' + str(ms_results['la_extant'][msc['ms']]) + '\t' + str(round(msc['count'] * 1.0 / ms_results['la_extant'][msc['ms']], 3) if ms_results['la_extant'][msc['ms']] else 0) + '\n')

            csv_file.close()

    def harmonizationsByLayer(s, h_label):
        c = s.config
        csvFile = c.get('outputFolder') + h_label + '-by-layer.csv'
        with open(csvFile, 'w+') as csv_file:
            for ms_results in s.results['reference_mss']:
                csv_file.write(ms_results['ms'] + '\n')
                csv_file.write('Layer\tVariation Units\tPossible Parallels\t' + ms_results['ms'] + ' Parallels\t' + ms_results['ms'] + ' Ratio\n')

                if not HarmAnalyzer.NO_MAJ:
                    csv_file.write('Majority Greek\t' + str(ms_results['rdg_count_byz']) + '\t' + str(ms_results['rdg_count_byz_possible']) + '\t' + str(ms_results['rdg_count_byz_parallel']) + '\t' + str(ms_results['pc_byz_parallels']) + '\n')

                csv_file.write('Non-majority Greek\t' + str(ms_results['rdg_count_nonbyz_greek']) + '\t' + str(ms_results['rdg_count_nonbyz_greek_possible']) + '\t' + str(ms_results['rdg_count_nonbyz_greek_parallel']) + '\t' + str(ms_results['pc_nonbyz_parallels']) + '\n')

                csv_file.write('Latin\t' + str(ms_results['rdg_count_latin_layer']) + '\t' + str(ms_results['rdg_count_latin_layer_possible']) + '\t' + str(ms_results['rdg_count_latin_parallel']) + '\t' + str(ms_results['pc_latin_parallels']) + '\n')

                csv_file.write('Singular\t' + str(ms_results['rdg_count_singular']) + '\t' + str(ms_results['rdg_count_singular_possible']) + '\t' + str(ms_results['rdg_count_singular_parallel']) + '\t' + str(ms_results['pc_singular_parallels']) + '\n')

                if not HarmAnalyzer.NO_MAJ:
                    csv_file.write('Total\t' + str(ms_results['vu_count']) + '\t' + str(ms_results['vu_count_w_parallel']) + '\t' + str(ms_results['rdg_count_w_parallel']) + '\t' + str(ms_results['pc_parallels']) + '\n')
                else:
                    csv_file.write('Total\t' + str(ms_results['vu_count']))

                csv_file.write('\n')

            if not HarmAnalyzer.NO_MAJ:
                csv_file.write('Attestation Ratio of Possible Non-majority Parallels in Select Manuscripts\n')
                csv_file.write('Manuscript\tVariation Units\tPossible Parallels\tManuscript Parallels\tRatio of Attested to Possible Parallels\n')
                for ms_results in s.results['reference_mss']:
                    csv_file.write(ms_results['ms'] + '\t')
                    csv_file.write(str(ms_results['rdg_count_nonbyz_greek']) + '\t')
                    csv_file.write(str(ms_results['rdg_count_nonbyz_greek_possible']) + '\t')
                    csv_file.write(str(ms_results['rdg_count_nonbyz_greek_parallel']) + '\t')
                    csv_file.write(str(ms_results['pc_nonbyz_parallels']) + '\n')
            
            csv_file.close()

    def computeLayer(s, v_label, reading, refMS):
        c = s.config
        if '35' in reading['mss']:
            return 'M'
        if refMS == '05':
            latinLayerVariants = c.get('latinLayerVariants').split(u'|')
            return 'L' if v_label in latinLayerVariants else 'G'
        else:
            latin_mss = []
            greek_mss = []
            for ms in reading['mss']:
                if ms == refMS:
                    continue
                if s.isLatinMS(ms):
                    if ms[:2] == 'VL': ms = ms[2:]
                    latin_mss.append(ms)
                else:
                    greek_mss.append(ms)
            return 'L' if isLatinLayer(len(greek_mss), len(latin_mss)) else 'G'

    def isLatinMS(s, ms):
        if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
            return True
        return False

    def vuGetInitialReading(s, vu):
        for rdg in vu['readings']:
            if rdg['na28'] == '1':
                return rdg
        return None

    def vuCountInitialReadings(s, vu):
        counter = 0
        for rdg in vu['readings']:
            if rdg['na28'] == '1':
                counter = counter + 1
        return counter

    def vuGetManuscriptReading(s, vu, ms):
        for rdg in vu['readings']:
            if ms in rdg['mss']:
                return rdg
        return None

    def vuHasManuscript(s, vu, ms):
        for rdg in vu['readings']:
            if ms in rdg['mss']:
                return True
        return False

    def vuHasNonInitialParallel(s, vu):
        for rdg in vu['readings']:
            if rdg['na28'] == '1':
                continue

            if rdg['parallels']:
                return True
        return False

    def vuHasNonByzantineParallel(s, vu):
        for rdg in vu['readings']:
            if '35' in rdg['mss']:
                continue

            if rdg['parallels']:
                return True
        return False

    def vuHasParallel(s, vu):
        for rdg in vu['readings']:
            if rdg['parallels']:
                return True
        return False

    def computeReferenceAgreements(s, refMS):
        c = s.config

        map_M = {}
        map_G = {}
        map_L = {}
        greekMSS = c.get('greekMSS')
        for ms in greekMSS:
            map_M[ms] = 0
            map_G[ms] = 0
            map_L[ms] = 0

        latinMSS = c.get('latinMSS')
        for ms in latinMSS:
            map_M[ms] = 0
            map_G[ms] = 0
            map_L[ms] = 0

        ms_results = {}
        for res in s.results['reference_mss']:
            if res['ms'] == refMS:
                ms_results = res
                break

        greekMSS = c.get('greekMSS')
        latinMSS = c.get('latinMSS')

        # Majority layer
        ms_results['bz_mss'] = []
        ms_results['bz_extant'] = {}
        for gms in greekMSS:
            ms_results['bz_extant'][gms] = 0
        for lms in latinMSS:
            ms_results['bz_extant'][lms] = 0
        for r_id in ms_results['byz_parallels']:
            rdg = s.reading_map[r_id]
            for ms in rdg['mss']:
                map_M[ms] = map_M[ms] + 1
            for gms in greekMSS:
                if s.vuHasManuscript(rdg['vu'], gms):
                    ms_results['bz_extant'][gms] = ms_results['bz_extant'][gms] + 1
            for lms in latinMSS:
                if s.vuHasManuscript(rdg['vu'], lms):
                    ms_results['bz_extant'][lms] = ms_results['bz_extant'][lms] + 1
        for ms, count in map_M.iteritems():
            ms_results['bz_mss'].append({'ms': ms, 'count': count, 'extant': ms_results['bz_extant'][ms]})
        ms_results['bz_mss'] = sorted(ms_results['bz_mss'], cmp=sortMSCounts)

        # Greek layer
        ms_results['gr_mss'] = []
        ms_results['gr_extant'] = {}
        for gms in greekMSS:
            ms_results['gr_extant'][gms] = 0
        for lms in latinMSS:
            ms_results['gr_extant'][lms] = 0
        for r_id in ms_results['greek_parallels']:
            rdg = s.reading_map[r_id]
            for ms in rdg['mss']:
                map_G[ms] = map_G[ms] + 1
            for gms in greekMSS:
                if s.vuHasManuscript(rdg['vu'], gms):
                    ms_results['gr_extant'][gms] = ms_results['gr_extant'][gms] + 1
            for lms in latinMSS:
                if s.vuHasManuscript(rdg['vu'], lms):
                    ms_results['gr_extant'][lms] = ms_results['gr_extant'][lms] + 1
        for ms, count in map_G.iteritems():
            ms_results['gr_mss'].append({'ms': ms, 'count': count, 'extant': ms_results['gr_extant'][ms]})
        ms_results['gr_mss'] = sorted(ms_results['gr_mss'], cmp=sortMSCounts)

        # Latin layer
        ms_results['la_mss'] = []
        ms_results['la_extant'] = {}
        for gms in greekMSS:
            ms_results['la_extant'][gms] = 0
        for lms in latinMSS:
            ms_results['la_extant'][lms] = 0
        for r_id in ms_results['latin_parallels']:
            rdg = s.reading_map[r_id]
            for ms in rdg['mss']:
                map_L[ms] = map_L[ms] + 1
            for gms in greekMSS:
                if s.vuHasManuscript(rdg['vu'], gms):
                    ms_results['la_extant'][gms] = ms_results['la_extant'][gms] + 1
            for lms in latinMSS:
                if s.vuHasManuscript(rdg['vu'], lms):
                    ms_results['la_extant'][lms] = ms_results['la_extant'][lms] + 1
        for ms, count in map_L.iteritems():
            ms_results['la_mss'].append({'ms': ms, 'count': count, 'extant': ms_results['la_extant'][ms]})
        ms_results['la_mss'] = sorted(ms_results['la_mss'], cmp=sortMSCounts)

    def computeResults(s, ms):
        s.info('Computing harmonization results for', ms)
        ms_results = {}
        ms_results['ms'] = ms
        s.results['reference_mss'].append(ms_results)

        vus = []
        vus_w_parallel = []
        vus_w_non_init_parallel = []
        vus_w_non_byz_parallel = []
        vus_w_non_byz_or_init_parallel = []

        rdgs_w_parallel = []
        rdgs_w_non_init_parallel = []
        rdgs_w_non_byz_parallel = []
        rdgs_w_non_byz_or_init_parallel = []

        noparl_rdgs_against_init_parallel = []
        rdgs_against_init_parallel = []
        rdgs_with_init_parallel = []

        singular_layer = []
        latin_layer = []
        greek_layer = []
        byz_layer = []

        singular_layer_possible = []
        latin_layer_possible = []
        greek_layer_possible = []
        byz_layer_possible = []

        singular_layer_hm = []
        latin_layer_hm = []
        greek_layer_hm = []
        byz_layer_hm = []

        initial_parallels = []

        for vu in s.vus:
            if s.vuHasManuscript(vu, ms):
                init_count = s.vuCountInitialReadings(vu)
                if init_count > 1 and vu['layer'] != 'M' and vu['layer'] != 'NA':
                    s.info('Multiple initial readings at chapter', vu['chapter'], ', verse', vu['start_verse'], ', index', vu['start_addrs'])

                init_rdg = s.vuGetInitialReading(vu)
                init_parallel = init_rdg['parallels'] if init_rdg else ''
                if init_parallel:
                    initial_parallels.append(vu['label'])

                ms_rdg = s.vuGetManuscriptReading(vu, ms)
                ms_parallel = ms_rdg['parallels']

                if HarmAnalyzer.NO_MAJ and vu['layer'] == 'M':
                    continue

                if init_parallel and init_rdg['reading_id'] == ms_rdg['reading_id']:
                    rdgs_with_init_parallel.append(vu['label'])
                elif init_parallel and init_rdg['reading_id'] != ms_rdg['reading_id']:
                    rdgs_against_init_parallel.append(vu['label'])
                    if not ms_parallel:
                        noparl_rdgs_against_init_parallel.append(vu['label'])

                if len(ms_rdg['mss']) == 1 or (ms == '05' and len(ms_rdg['mss']) == 2 and 'VL5' in ms_rdg['mss']):
                    singular_layer.append(vu['label'])
                    if s.vuHasParallel(vu):
                        singular_layer_possible.append(vu['label'])
                    if ms_parallel:
                        singular_layer_hm.append(ms_rdg['reading_id'])
                elif not s.isLatinMS(ms):
                    layer = s.computeLayer(vu['label'], ms_rdg, ms)
                    if layer == 'L':
                        latin_layer.append(vu['label'])
                        if s.vuHasParallel(vu):
                            latin_layer_possible.append(vu['label'])
                        if ms_parallel:
                            latin_layer_hm.append(ms_rdg['reading_id'])
                    elif layer == 'G':
                        greek_layer.append(vu['label'])
                        if s.vuHasParallel(vu):
                            greek_layer_possible.append(vu['label'])
                        if ms_parallel:
                            greek_layer_hm.append(ms_rdg['reading_id'])
                    else:
                        byz_layer.append(vu['label'])
                        if s.vuHasParallel(vu):
                            byz_layer_possible.append(vu['label'])
                        if ms_parallel:
                            byz_layer_hm.append(ms_rdg['reading_id'])

                vus.append(vu['label'])
                if s.vuHasParallel(vu):
                    vus_w_parallel.append(vu['label'])
                    if ms_parallel:
                        rdgs_w_parallel.append(vu['label'])
                if s.vuHasNonInitialParallel(vu):
                    vus_w_non_init_parallel.append(vu['label'])
                    if ms_parallel:
                        rdgs_w_non_init_parallel.append(vu['label'])
                    if s.vuHasNonByzantineParallel(vu):
                        vus_w_non_byz_or_init_parallel.append(vu['label'])
                        if ms_parallel:
                            rdgs_w_non_byz_or_init_parallel.append(vu['label'])
                if s.vuHasNonByzantineParallel(vu):
                    vus_w_non_byz_parallel.append(vu['label'])
                    if ms_parallel:
                        rdgs_w_non_byz_parallel.append(vu['label'])

        ms_results['vu_count'] = len(s.vus)

        ms_results['vu_count_w_parallel'] = len(vus_w_parallel)
        ms_results['rdg_count_w_parallel'] = len(rdgs_w_parallel)
        ms_results['pc_parallels'] = round(ms_results['rdg_count_w_parallel'] * 1.0 /  ms_results['vu_count_w_parallel'], 3) if ms_results['vu_count_w_parallel'] != 0 else 0

        ms_results['initial_parallel_count'] = len(initial_parallels)
        ms_results['rdg_count_against_init_parallel'] = len(rdgs_against_init_parallel)
        ms_results['rdg_count_against_init_parallel_w_no_parallel'] = len(noparl_rdgs_against_init_parallel)
        ms_results['rdg_count_with_init_parallel'] = len(rdgs_with_init_parallel)

        ms_results['pc_against_init_parallels'] = round(ms_results['rdg_count_against_init_parallel'] * 1.0 /  ms_results['initial_parallel_count'], 3) if ms_results['initial_parallel_count'] != 0 else 0
        ms_results['pc_with_init_parallels'] = round(ms_results['rdg_count_with_init_parallel'] * 1.0 /  ms_results['initial_parallel_count'], 3) if ms_results['initial_parallel_count'] != 0 else 0

        ms_results['vu_count_w_non_init_parallel'] = len(vus_w_non_init_parallel)
        ms_results['rdg_count_w_non_init_parallel'] = len(rdgs_w_non_init_parallel)
        ms_results['pc_non_init_parallels'] = round(ms_results['rdg_count_w_non_init_parallel'] * 1.0 /  ms_results['vu_count_w_non_init_parallel'], 3) if ms_results['vu_count_w_non_init_parallel'] != 0 else 0

        ms_results['vu_count_w_non_byz_parallel'] = len(vus_w_non_byz_parallel)
        ms_results['rdg_count_w_non_byz_parallel'] = len(rdgs_w_non_byz_parallel)
        ms_results['pc_non_byz_parallels'] = round(ms_results['rdg_count_w_non_byz_parallel'] * 1.0 /  ms_results['vu_count_w_non_byz_parallel'], 3) if ms_results['vu_count_w_non_byz_parallel'] != 0 else 0

        ms_results['vu_count_w_non_byz_or_init_parallel'] = len(vus_w_non_byz_or_init_parallel)
        ms_results['rdg_count_w_non_byz_or_init_parallel'] = len(rdgs_w_non_byz_or_init_parallel)
        ms_results['pc_non_byz_or_init_parallels'] = round(ms_results['rdg_count_w_non_byz_or_init_parallel'] * 1.0 /  ms_results['vu_count_w_non_byz_or_init_parallel'], 3) if ms_results['vu_count_w_non_byz_or_init_parallel'] != 0 else 0

        ms_results['rdg_count_singular'] = len(singular_layer)
        ms_results['rdg_count_singular_possible'] = len(singular_layer_possible)
        ms_results['rdg_count_singular_parallel'] = len(singular_layer_hm)
        ms_results['pc_singular_parallels'] = round(ms_results['rdg_count_singular_parallel'] * 1.0 /  ms_results['rdg_count_singular_possible'], 3) if ms_results['rdg_count_singular_possible'] != 0 else 0

        ms_results['rdg_count_latin_layer'] = len(latin_layer)
        ms_results['rdg_count_latin_layer_possible'] = len(latin_layer_possible)
        ms_results['rdg_count_latin_parallel'] = len(latin_layer_hm)
        ms_results['latin_parallels'] = latin_layer_hm
        ms_results['pc_latin_parallels'] = round(ms_results['rdg_count_latin_parallel'] * 1.0 /  ms_results['rdg_count_latin_layer_possible'], 3) if ms_results['rdg_count_latin_layer_possible'] != 0 else 0

        ms_results['rdg_count_nonbyz_greek'] = len(greek_layer)
        ms_results['rdg_count_nonbyz_greek_possible'] = len(greek_layer_possible)
        ms_results['rdg_count_nonbyz_greek_parallel'] = len(greek_layer_hm)
        ms_results['greek_parallels'] = greek_layer_hm
        ms_results['pc_nonbyz_parallels'] = round(ms_results['rdg_count_nonbyz_greek_parallel'] * 1.0 /  ms_results['rdg_count_nonbyz_greek_possible'], 3) if ms_results['rdg_count_nonbyz_greek_possible'] != 0 else 0

        ms_results['rdg_count_byz'] = len(byz_layer)
        ms_results['rdg_count_byz_possible'] = len(byz_layer_possible)
        ms_results['rdg_count_byz_parallel'] = len(byz_layer_hm)
        ms_results['byz_parallels'] = byz_layer_hm
        ms_results['pc_byz_parallels'] = round(ms_results['rdg_count_byz_parallel'] * 1.0 /  ms_results['rdg_count_byz_possible'], 3) if ms_results['rdg_count_byz_possible'] != 0 else 0

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        h_label = ''
        harm_file = None
        cachefile = None
        if o.file:
            h_label = o.file
            harm_file = c.get('inputFolder') + h_label + '.csv'
        else:
            h_label = c.get('harmonizationFile')
            harm_file = c.get('inputFolder') + h_label + '.csv'

        csvdata = ''
        with open(harm_file, 'r') as file:
            s.info('reading', harm_file)
            csvdata = file.read().decode('utf-8')
            file.close()

        vu = {}
        col_names = []
        rows = csvdata.split('\n')
        for rdx, row in enumerate(rows):
            if rdx == 0: # colnames
                col_names = row.split('\t')
                if col_names[0] != 'reading_id':
                    raise ValueError('reading_id must be first column')
                continue

            parts = row.split('\t')
            if len(parts) == 1:
                continue

            rdg = {}
            for cdx, col_name in enumerate(col_names):
                part = parts[cdx]
                if col_name == 'reading_id':
                    # 14.1.36a
                    # 1.7.7-10,12-13,16-19,21-22,8.1-2,4-5,7-8a
                    rs = re.search(r'((\d{1,2})\.(\d{1,2})\.([0-9\-,]{1,}))(,(\d{1,2})\.([0-9\-,]{1,})){0,1}(,(\d{1,2})\.([0-9\-,]{1,})){0,1}([a-z])', part)
                    if rs and rs.group(11) == 'a':
                        if vu:
                            s.vus.append(vu)

                        vu = {}
                        vu['label'] = rs.group(1)
                        if rs.group(5):
                            vu['label'] = vu['label'] + rs.group(5)
                        if rs.group(8):
                            vu['label'] = vu['label'] + rs.group(8)
                        vu['chapter'] = rs.group(2)
                        vu['start_verse'] = rs.group(3)
                        vu['start_addrs'] = rs.group(4)
                        if rs.group(6) and rs.group(7):
                            vu['end_verse'] = rs.group(6)
                            vu['end_addrs'] = rs.group(7)
                        vu['readings'] = []
                    rdg['code'] = rs.group(11)
                    rdg['reading_id'] = vu['label'] + rdg['code']
                    rdg['mss'] = []
                    vu['readings'].append(rdg)
                    rdg['vu'] = vu
                    s.reading_map[vu['label'] + rdg['code']] = rdg
                    continue

                if col_name == 'sort_id':
                    continue

                if col_name == 'reading_text':
                    rdg['reading_text'] = part
                    continue

                if col_name == 'is_singular':
                    rdg['is_singular'] = part
                    continue

                if col_name == 'is_latin':
                    rdg['is_latin'] = part
                    continue

                if col_name == 'parallels':
                    rdg['parallels'] = part
                    continue

                if col_name == 'synoptic_rdEgs':
                    rdg['synoptic_readings'] = part
                    continue

                if col_name == 'layer':
                    vu['layer'] = part
                    continue

                if col_name == 'na28':
                    rdg['na28'] = part
                    continue

                if part == '1':
                    rdg['mss'].append(col_name)

        if vu:
            s.vus.append(vu)

        if o.refMSS:
            s.refMS_IDs = o.refMSS.split(',')
        else:
            s.refMS_IDs = c.get('showSingulars')

        inits_w_parallel = []
        byzes_w_parallel = []
        vus_w_parallel = []
        vu_count_w_parallel = 0
        for vu in s.vus:
            init_rdg = s.vuGetInitialReading(vu)
            init_parallel = init_rdg['parallels'] if init_rdg else ''
            if init_parallel:
                inits_w_parallel.append(vu['label'])

            byz_rdg = s.vuGetManuscriptReading(vu, '35')
            byz_parallel = byz_rdg['parallels'] if byz_rdg else ''
            if byz_parallel:
                byzes_w_parallel.append(vu['label'])

            if s.vuHasParallel(vu):
                vus_w_parallel.append(vu['label'])

        s.results['variation_units'] = len(s.vus)
        s.results['vu_count_w_parallel'] = len(vus_w_parallel)
        s.results['init_count_w_parallel'] = len(inits_w_parallel)
        s.results['byz_count_w_parallel'] = len(byzes_w_parallel)
        s.results['reference_mss'] = []
        for ms in s.refMS_IDs:
            if HarmAnalyzer.NO_MAJ and ms != '05':
                continue
            s.computeResults(ms)
            s.computeReferenceAgreements(ms)

            s.harmonizationsByLayer(h_label)
            s.harmonizationsByAgreement(ms, h_label)

        result_file = c.get('outputFolder') + h_label + '-results.json'
        jdata = json.dumps(s.results, ensure_ascii=False)
        with open(result_file, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

        s.info('Done')

# Produce harmonization analysis for reference MSS
# harmAnalyzer.py -v -f harm-16
HarmAnalyzer().main(sys.argv[1:])
