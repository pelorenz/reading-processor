#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, re
from collections import OrderedDict
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

        ms_results = OrderedDict()
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
                csv_file.write('Layer\tVariation Units\tPossible Parallels\t' + ms_results['ms'] + ' Parallels\t' + ms_results['ms'] + ' Ratio\tPossible Non-initial Parallels\t' + ms_results['ms'] + ' Non-initial Parallels\t' + ms_results['ms'] + ' Non-initial Ratio\n')

                if not HarmAnalyzer.NO_MAJ:
                    csv_file.write('Majority Greek\t' + str(ms_results['rdg_count_byz']) + '\t' + str(ms_results['rdg_count_byz_possible']) + '\t' + str(ms_results['rdg_count_byz_parallel']) + '\t' + str(ms_results['pc_byz_parallels']) + '\n')

                csv_file.write('Non-majority Greek\t' + str(ms_results['rdg_count_nonbyz_greek']) + '\t' + str(ms_results['rdg_count_nonbyz_greek_possible']) + '\t' + str(ms_results['rdg_count_nonbyz_greek_parallel']) + '\t' + str(ms_results['pc_nonbyz_parallels']) + '\t' + str(len(ms_results['greek_noninit_p'])) + '\t' + str(len(ms_results['greek_noninit_p_for'])) + '\t' + str(ms_results['pc_greek_noninit_p_for']) + '\n')

                csv_file.write('Latin\t' + str(ms_results['rdg_count_latin_layer']) + '\t' + str(ms_results['rdg_count_latin_layer_possible']) + '\t' + str(ms_results['rdg_count_latin_parallel']) + '\t' + str(ms_results['pc_latin_parallels']) + '\t' + str(len(ms_results['latin_noninit_p'])) + '\t' + str(len(ms_results['latin_noninit_p_for'])) + '\t' + str(ms_results['pc_latin_noninit_p_for']) + '\n')

                csv_file.write('Singular\t' + str(ms_results['rdg_count_singular']) + '\t' + str(ms_results['rdg_count_singular_possible']) + '\t' + str(ms_results['rdg_count_singular_parallel']) + '\t' + str(ms_results['pc_singular_parallels']) + '\t' + str(len(ms_results['sing_noninit_p'])) + '\t' + str(len(ms_results['sing_noninit_p_for'])) + '\t' + str(ms_results['pc_sing_noninit_p_for']) + '\n')

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

    def isSubSingular(s, v_label, reading, refMS):
        c = s.config
        if refMS == '05':
            subsingular = c.get('subsingularVariants').split(u'|')
            if v_label in subsingular:
                return True
            else:
                return False
        else:
            return False

    def computeLayer(s, v_label, reading, refMS):
        c = s.config
        if '35' in reading['mss']:
            return 'M'
        if refMS == '05':
            latinCore = c.get('latinLayerCoreVariants').split(u'|')
            latinMulti = c.get('latinLayerMultiVariants').split(u'|')
            if v_label in latinCore or v_label in latinMulti:
                return 'L'
            else:
                return 'G'
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

        sing_initial_p = []
        latin_initial_p = []
        greek_initial_p = []

        sing_noninit_p = []
        latin_noninit_p = []
        greek_noninit_p = []

        latin_initial_p_for = []
        greek_initial_p_for = []

        sing_noninit_p_for = []
        latin_noninit_p_for = []
        greek_noninit_p_for = []

        sing_initial_p_against = []
        latin_initial_p_against = []
        greek_initial_p_against = []

        sing_noninit_p_against = []
        latin_noninit_p_against = []
        greek_noninit_p_against = []

        noparl_sing_initial_p_against = []
        noparl_latin_initial_p_against = []
        noparl_greek_initial_p_against = []

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
                init_reading = init_rdg['reading_text'] if init_rdg else ''
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

                if len(ms_rdg['mss']) == 1 or (ms == '05' and len(ms_rdg['mss']) == 2 and 'VL5' in ms_rdg['mss']) or s.isSubSingular(vu['label'], ms_rdg, ms):
                    singular_layer.append(vu['label'])
                    if s.vuHasParallel(vu):
                        singular_layer_possible.append(vu['label'])
                    if ms_parallel:
                        singular_layer_hm.append(ms_rdg['reading_id'])
                    if init_parallel:
                        sing_initial_p.append(vu['label'])
                        sing_initial_p_against = sing_initial_p # same list!
                        if not ms_parallel:
                            noparl_sing_initial_p_against.append((vu['label'], init_parallel, init_reading))
                    if s.vuHasNonInitialParallel(vu):
                        sing_noninit_p.append(vu['label'])
                        if ms_parallel:
                            sing_noninit_p_for.append(vu['label'])
                        else:
                            sing_noninit_p_against.append(vu['label'])
                elif not s.isLatinMS(ms):
                    layer = s.computeLayer(vu['label'], ms_rdg, ms)
                    if layer == 'L':
                        latin_layer.append(vu['label'])
                        if s.vuHasParallel(vu):
                            latin_layer_possible.append(vu['label'])
                        if ms_parallel:
                            latin_layer_hm.append(ms_rdg['reading_id'])
                        if init_parallel:
                            latin_initial_p.append(vu['label'])
                            if init_rdg['reading_id'] == ms_rdg['reading_id']:
                                latin_initial_p_for.append(vu['label'])
                            elif init_rdg['reading_id'] != ms_rdg['reading_id']:
                                latin_initial_p_against.append(vu['label'])
                                if not ms_parallel:
                                    noparl_latin_initial_p_against.append((vu['label'], init_parallel, init_reading))
                        if s.vuHasNonInitialParallel(vu):
                            latin_noninit_p.append(vu['label'])
                            if (not init_rdg or init_rdg['reading_id'] != ms_rdg['reading_id']):
                                if ms_parallel:
                                    latin_noninit_p_for.append(vu['label'])
                                else:
                                    latin_noninit_p_against.append(vu['label'])
                    elif layer == 'G':
                        greek_layer.append(vu['label'])
                        if s.vuHasParallel(vu):
                            greek_layer_possible.append(vu['label'])
                        if ms_parallel:
                            greek_layer_hm.append(ms_rdg['reading_id'])
                        if init_parallel:
                            greek_initial_p.append(vu['label'])
                            if init_rdg['reading_id'] == ms_rdg['reading_id']:
                                greek_initial_p_for.append(vu['label'])
                            elif init_rdg['reading_id'] != ms_rdg['reading_id']:
                                greek_initial_p_against.append(vu['label'])
                                if not ms_parallel:
                                    noparl_greek_initial_p_against.append((vu['label'], init_parallel, init_reading))
                        if s.vuHasNonInitialParallel(vu):
                            greek_noninit_p.append(vu['label'])
                            if (not init_rdg or init_rdg['reading_id'] != ms_rdg['reading_id']):
                                if ms_parallel:
                                    greek_noninit_p_for.append(vu['label'])
                                else:
                                    greek_noninit_p_against.append(vu['label'])
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
            else:
                s.info('VU chapter', vu['chapter'], ', verse', vu['start_verse'], ', index', vu['start_addrs'], ' not attested by', ms)

        ms_results['vu_count'] = len(vus)

        ms_results['vu_count_w_parallel'] = len(vus_w_parallel)
        ms_results['rdg_count_w_parallel'] = len(rdgs_w_parallel)
        ms_results['pc_parallels'] = round(ms_results['rdg_count_w_parallel'] * 1.0 /  ms_results['vu_count_w_parallel'], 3) if ms_results['vu_count_w_parallel'] != 0 else 0

        ms_results['initial_parallel_count'] = len(initial_parallels)
        ms_results['rdg_count_against_init_parallel'] = len(rdgs_against_init_parallel)
        ms_results['rdg_count_against_init_parallel_w_no_parallel'] = len(noparl_rdgs_against_init_parallel)
        ms_results['rdg_count_with_init_parallel'] = len(rdgs_with_init_parallel)

        ms_results['pc_with_init_parallels'] = round(ms_results['rdg_count_with_init_parallel'] * 1.0 /  ms_results['initial_parallel_count'], 3) if ms_results['initial_parallel_count'] != 0 else 0
        ms_results['pc_against_init_parallels'] = round(ms_results['rdg_count_against_init_parallel'] * 1.0 /  ms_results['initial_parallel_count'], 3) if ms_results['initial_parallel_count'] != 0 else 0
        ms_results['pc_against_init_parallels_w_no_parallel'] = round(ms_results['rdg_count_against_init_parallel_w_no_parallel'] * 1.0 /  ms_results['rdg_count_against_init_parallel'], 3) if ms_results['initial_parallel_count'] != 0 else 0

        ms_results['vu_count_w_non_init_parallel'] = len(vus_w_non_init_parallel)
        ms_results['rdg_count_w_non_init_parallel'] = len(rdgs_w_non_init_parallel)
        ms_results['pc_non_init_parallels'] = round(ms_results['rdg_count_w_non_init_parallel'] * 1.0 /  ms_results['vu_count_w_non_init_parallel'], 3) if ms_results['vu_count_w_non_init_parallel'] != 0 else 0

        ms_results['vu_count_w_non_byz_parallel'] = len(vus_w_non_byz_parallel)
        ms_results['rdg_count_w_non_byz_parallel'] = len(rdgs_w_non_byz_parallel)
        ms_results['pc_non_byz_parallels'] = round(ms_results['rdg_count_w_non_byz_parallel'] * 1.0 /  ms_results['vu_count_w_non_byz_parallel'], 3) if ms_results['vu_count_w_non_byz_parallel'] != 0 else 0

        ms_results['vu_count_w_non_byz_or_init_parallel'] = len(vus_w_non_byz_or_init_parallel)
        ms_results['rdg_count_w_non_byz_or_init_parallel'] = len(rdgs_w_non_byz_or_init_parallel)
        ms_results['pc_non_byz_or_init_parallels'] = round(ms_results['rdg_count_w_non_byz_or_init_parallel'] * 1.0 /  ms_results['vu_count_w_non_byz_or_init_parallel'], 3) if ms_results['vu_count_w_non_byz_or_init_parallel'] != 0 else 0

        ms_results['singular_layer'] = singular_layer
        ms_results['rdg_count_singular'] = len(singular_layer)
        ms_results['rdg_count_singular_possible'] = len(singular_layer_possible)
        ms_results['rdg_count_singular_parallel'] = len(singular_layer_hm)
        ms_results['pc_singular_parallels'] = round(ms_results['rdg_count_singular_parallel'] * 1.0 /  ms_results['rdg_count_singular_possible'], 3) if ms_results['rdg_count_singular_possible'] != 0 else 0

        ms_results['sing_initial_p'] = sing_initial_p
        ms_results['sing_noninit_p'] = sing_noninit_p
        ms_results['sing_noninit_p_for'] = sing_noninit_p_for
        ms_results['sing_initial_p_against'] = sing_initial_p_against
        ms_results['sing_noninit_p_against'] = sing_noninit_p_against
        ms_results['pc_sing_noninit_p_for'] = round(len(ms_results['sing_noninit_p_for']) * 1.0 /  len(ms_results['sing_noninit_p']), 3) if len(ms_results['sing_noninit_p']) != 0 else 0
        ms_results['noparl_sing_initial_p_against'] = noparl_sing_initial_p_against

        ms_results['latin_layer'] = latin_layer
        ms_results['latin_initial_p'] = latin_initial_p
        ms_results['latin_noninit_p'] = latin_noninit_p
        ms_results['latin_initial_p_for'] = latin_initial_p_for
        ms_results['latin_noninit_p_for'] = latin_noninit_p_for
        ms_results['latin_initial_p_against'] = latin_initial_p_against
        ms_results['latin_noninit_p_against'] = latin_noninit_p_against
        ms_results['pc_latin_noninit_p_for'] = round(len(ms_results['latin_noninit_p_for']) * 1.0 /  len(ms_results['latin_noninit_p']), 3) if len(ms_results['latin_noninit_p']) != 0 else 0
        ms_results['noparl_latin_initial_p_against'] = noparl_latin_initial_p_against
        ms_results['rdg_count_latin_layer'] = len(latin_layer)
        ms_results['rdg_count_latin_layer_possible'] = len(latin_layer_possible)
        ms_results['rdg_count_latin_parallel'] = len(latin_layer_hm)
        ms_results['latin_parallels'] = latin_layer_hm
        ms_results['pc_latin_parallels'] = round(ms_results['rdg_count_latin_parallel'] * 1.0 /  ms_results['rdg_count_latin_layer_possible'], 3) if ms_results['rdg_count_latin_layer_possible'] != 0 else 0

        ms_results['greek_layer'] = greek_layer
        ms_results['greek_initial_p'] = greek_initial_p
        ms_results['greek_noninit_p'] = greek_noninit_p
        ms_results['greek_initial_p_for'] = greek_initial_p_for
        ms_results['greek_noninit_p_for'] = greek_noninit_p_for
        ms_results['greek_initial_p_against'] = greek_initial_p_against
        ms_results['greek_noninit_p_against'] = greek_noninit_p_against
        ms_results['pc_greek_noninit_p_for'] = round(len(ms_results['greek_noninit_p_for']) * 1.0 / len(ms_results['greek_noninit_p']), 3) if len(ms_results['greek_noninit_p']) != 0 else 0
        ms_results['noparl_greek_initial_p_against'] = noparl_greek_initial_p_against
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

        result_file = c.get('outputFolder') + h_label + '-init-readings.csv'
        with open(result_file, 'w+') as file:
            for ms in s.results['reference_mss']:
                lyr = ''
                file.write((u'All Singular Against Initial Parallel without Alternative (Initial Readings)\t\t').encode('UTF-8'))
                for idx, (label, init_p, init_r) in enumerate(ms['noparl_sing_initial_p_against']):
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + init_r
                file.write((lyr + u'\n\n').encode('UTF-8'))

                lyr = ''
                file.write((u'All Latin Against Initial Parallel without Alternative (Initial Readings)\t\t').encode('UTF-8'))
                for idx, (label, init_p, init_r) in enumerate(ms['noparl_latin_initial_p_against']):
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + init_r
                file.write((lyr + u'\n\n').encode('UTF-8'))

                lyr = ''
                file.write((u'All Greek Against Initial Parallel without Alternative (Initial Readings)\t\t').encode('UTF-8'))
                for idx, (label, init_p, init_r) in enumerate(ms['noparl_greek_initial_p_against']):
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + init_r
                file.write((lyr + u'\n\n').encode('UTF-8'))

            file.close()

        result_file = c.get('outputFolder') + h_label + '-results.csv'
        with open(result_file, 'w+') as file:
            file.write('VUs\t\t' + str(s.results['variation_units']) + '\n')
            file.write('VUs with ||\t\t' + str(s.results['vu_count_w_parallel']) + '\n')
            file.write('Initial Rs with ||\t\t' + str(s.results['init_count_w_parallel']) + '\n')
            file.write('Byzantine Rs with ||\t\t' + str(s.results['byz_count_w_parallel']) + '\n')
            file.write('\n')
            for ms in s.results['reference_mss']:
                file.write('MS ID\t\t' + ms['ms'] + '\n')

                file.write('Rs Agreeing with Initial ||\t\t' + str(ms['rdg_count_with_init_parallel']) + '\n')
                file.write('% Agreeing with Initial ||\t' + str(ms['rdg_count_with_init_parallel']) + '/' +  str(ms['initial_parallel_count']) + '\t' + str(ms['pc_with_init_parallels']) + '\n')
                file.write('\n')

                file.write('Rs Diverging from Initial || (with or without ||)\t\t' + str(ms['rdg_count_against_init_parallel']) + '\n')
                file.write('% Diverging from Initial ||\t' + str(ms['rdg_count_against_init_parallel']) + '/' +  str(ms['initial_parallel_count']) + '\t' + str(ms['pc_against_init_parallels']) + '\n')
                file.write('\n')

                file.write('Rs Diverging from Initial || (without ||)\t\t' + str(ms['rdg_count_against_init_parallel_w_no_parallel']) + '\n')
                file.write('% Diverging from Initial || (without ||)\t' + str(ms['rdg_count_against_init_parallel_w_no_parallel']) + '/' +  str(ms['rdg_count_against_init_parallel']) + '\t' + str(ms['pc_against_init_parallels_w_no_parallel']) + '\n')
                file.write('\n')

                file.write('VUs with Non-Initial ||\t\t' + str(ms['vu_count_w_non_init_parallel']) + '\n')
                file.write('Non-Initial Rs with ||\t\t' + str(ms['rdg_count_w_non_init_parallel']) + '\n')
                file.write('% Non-Initial ||s\t' + str(ms['rdg_count_w_non_init_parallel']) + '/' +  str(ms['vu_count_w_non_init_parallel']) + '\t' + str(ms['pc_non_init_parallels']) + '\n')
                file.write('\n')

                file.write('VUs with Non-Byzantine ||\t\t' + str(ms['vu_count_w_non_byz_parallel']) + '\n')
                file.write('Non-Byzantine Rs with ||\t\t' + str(ms['rdg_count_w_non_byz_parallel']) + '\n')
                file.write('% Non-Byzantine ||s\t' + str(ms['rdg_count_w_non_byz_parallel']) + '/' +  str(ms['vu_count_w_non_byz_parallel']) + '\t' + str(ms['pc_non_byz_parallels']) + '\n')
                file.write('\n')

                file.write('VUs with Neither Initial nor Byzantine ||\t\t' + str(ms['vu_count_w_non_byz_or_init_parallel']) + '\n')
                file.write('Non-Initial and Non-Byzantine Rs with ||\t\t' + str(ms['rdg_count_w_non_byz_or_init_parallel']) + '\n')
                file.write('% Non-Initial and Non-Byzantine ||s\t' + str(ms['rdg_count_w_non_byz_or_init_parallel']) + '/' +  str(ms['vu_count_w_non_byz_or_init_parallel']) + '\t' + str(ms['pc_non_byz_or_init_parallels']) + '\n')
                file.write('\n')

                file.write('Singular Rs\t\t' + str(ms['rdg_count_singular']) + '\n')
                file.write('Singular Rs with Possible ||\t\t' + str(ms['rdg_count_singular_possible']) + '\n')
                file.write('Singular Rs with Attested ||\t\t' + str(ms['rdg_count_singular_parallel']) + '\n')
                file.write('% Singular ||s\t' + str(ms['rdg_count_singular_parallel']) + '/' +  str(ms['rdg_count_singular_possible']) + '\t' + str(ms['pc_singular_parallels']) + '\n')
                file.write('Singular VUs with Initial ||\t\t' + str(len(ms['sing_initial_p'])) + '\n')
                file.write('Singular Rs for Initial ||\t\t0\n')
                file.write('Singular Rs against Initial ||\t\t' + str(len(ms['sing_initial_p_against'])) + '\n')
                file.write('Singular Rs against Initial || (without ||)\t\t' + str(len(ms['noparl_sing_initial_p_against'])) + '\n')
                file.write('Singular VUs with Non-Initial ||\t\t' + str(len(ms['sing_noninit_p'])) + '\n')
                file.write('Singular Rs for Non-Initial ||\t\t' + str(len(ms['sing_noninit_p_for'])) + '\n')
                file.write('Singular Rs against Non-Initial ||\t\t' + str(len(ms['sing_noninit_p_against'])) + '\n')
                file.write('\n')

                file.write('Latin Rs\t\t' + str(ms['rdg_count_latin_layer']) + '\n')
                file.write('Latin Rs with Possible ||\t\t' + str(ms['rdg_count_latin_layer_possible']) + '\n')
                file.write('Latin Rs with Attested ||\t\t' + str(ms['rdg_count_latin_parallel']) + '\n')
                file.write('% Latin ||s\t' + str(ms['rdg_count_latin_parallel']) + '/' +  str(ms['rdg_count_latin_layer_possible']) + '\t' + str(ms['pc_latin_parallels']) + '\n')
                file.write('Latin VUs with Initial ||\t\t' + str(len(ms['latin_initial_p'])) + '\n')
                file.write('Latin Rs for Initial ||\t\t' + str(len(ms['latin_initial_p_for'])) + '\n')
                file.write('Latin Rs against Initial ||\t\t' + str(len(ms['latin_initial_p_against'])) + '\n')
                file.write('Latin Rs against Initial || (without ||)\t\t' + str(len(ms['noparl_latin_initial_p_against'])) + '\n')
                file.write('Latin VUs with Non-Initial ||\t\t' + str(len(ms['latin_noninit_p'])) + '\n')
                file.write('Latin Rs for Non-Initial ||\t\t' + str(len(ms['latin_noninit_p_for'])) + '\n')
                file.write('Latin Rs against Non-Initial ||\t\t' + str(len(ms['latin_noninit_p_against'])) + '\n')
                file.write('\n')

                file.write('Non-Byzantine Greek Rs\t\t' + str(ms['rdg_count_nonbyz_greek']) + '\n')
                file.write('Non-Byzantine Greek Rs with Possible ||\t\t' + str(ms['rdg_count_nonbyz_greek_possible']) + '\n')
                file.write('Non-Byzantine Greek Rs with Attested ||\t\t' + str(ms['rdg_count_nonbyz_greek_parallel']) + '\n')
                file.write('% Non-Byzantine Greek ||s\t' + str(ms['rdg_count_nonbyz_greek_parallel']) + '/' +  str(ms['rdg_count_nonbyz_greek_possible']) + '\t' + str(ms['pc_nonbyz_parallels']) + '\n')
                file.write('Non-Byzantine VUs with Initial ||\t\t' + str(len(ms['greek_initial_p'])) + '\n')
                file.write('Non-Byzantine Rs for Initial ||\t\t' + str(len(ms['greek_initial_p_for'])) + '\n')
                file.write('Non-Byzantine Rs against Initial ||\t\t' + str(len(ms['greek_initial_p_against'])) + '\n')
                file.write('Non-Byzantine Rs against Initial || (without ||)\t\t' + str(len(ms['noparl_greek_initial_p_against'])) + '\n')
                file.write('Non-Byzantine VUs with Non-Initial ||\t\t' + str(len(ms['greek_noninit_p'])) + '\n')
                file.write('Non-Byzantine Rs for Non-Initial ||\t\t' + str(len(ms['greek_noninit_p_for'])) + '\n')
                file.write('Non-Byzantine Rs against Non-Initial ||\t\t' + str(len(ms['greek_noninit_p_against'])) + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Singular Non-initial Parallels\t\t')
                for label in ms['sing_noninit_p_for']:
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + label
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Latin Non-initial Parallels\t\t')
                for label in ms['latin_noninit_p_for']:
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + label
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Greek Non-initial Parallels\t\t')
                for label in ms['greek_noninit_p_for']:
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + label
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Singular Against Initial Parallel without Alternative (Labels)\t\t')
                for idx, (label, init_p, init_r) in enumerate(ms['noparl_sing_initial_p_against']):
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + label
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Singular Against Initial Parallel without Alternative (Initial Parallels)\t\t')
                for idx, (label, init_p, init_r) in enumerate(ms['noparl_sing_initial_p_against']):
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + init_p
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Latin Against Initial Parallel without Alternative (Labels)\t\t')
                for idx, (label, init_p, init_r) in enumerate(ms['noparl_latin_initial_p_against']):
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + label
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Latin Against Initial Parallel without Alternative (Initial Parallels)\t\t')
                for idx, (label, init_p, init_r) in enumerate(ms['noparl_latin_initial_p_against']):
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + init_p
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Greek Against Initial Parallel without Alternative (Labels)\t\t')
                for idx, (label, init_p, init_r) in enumerate(ms['noparl_greek_initial_p_against']):
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + label
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Greek Against Initial Parallel without Alternative (Initial Parallels)\t\t')
                for idx, (label, init_p, init_r) in enumerate(ms['noparl_greek_initial_p_against']):
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + init_p
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Singular VUs\t\t')
                for label in ms['singular_layer']:
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + label
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Latin VUs\t\t')
                for label in ms['latin_layer']:
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + label
                file.write(lyr + '\n')
                file.write('\n')

                lyr = ''
                file.write('All Non-Byzantine Greek VUs\t\t')
                for label in ms['greek_layer']:
                    if lyr:
                        lyr = lyr + '|'
                    lyr = lyr + label
                file.write(lyr + '\n')

            file.close()

        s.info('Done')

# Produce harmonization analysis for reference MSS
# harmAnalyzer.py -v -f harm-16
HarmAnalyzer().main(sys.argv[1:])
