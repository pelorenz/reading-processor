#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, json, re, subprocess, itertools

import numpy as np
from object.jsonEncoder import *
from object.rangeManager import *
from object.truthTable import *
from object.util import *

from utility.config import *
from utility.options import *

class Dicer:

    CORE_GROUPS = ['F03', 'C565', 'F1', 'F13', 'CP45']

    def __init__(s):
        s.dicerFolder = 'dicer-results'
        s.statsFolder = 'static/stats/dicer/'
        s.range_id = ''
        s.rangeMgr = None
        s.qcaSet = 'basic'
        s.variantModel = None

        s.dicer_segments = []
        s.segment_min = 300

        s.doHauptliste = False
        s.doQCA = False
        s.doOffsets = False # include offsets in results
        s.segmentConfig = None

        s.latinLayerCore = []
        s.latinLayerMulti = []
        s.subsingular = []

        s.vu_count = 0
        s.no_retro_count = 0
        s.m_readings = []
        s.m_sg_readings = []
        s.na_readings = []
        s.d_readings = []
        s.l_readings = []
        s.s_readings = []
        s.s_05_retro_readings = []
        s.s_05VL5_readings = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def diceText(s, ms):
        c = s.config

        s.info('Dicing text')

        c_count = 1
        v_count = 0
        w_count = 0

        cur_c = 1
        cur_v = 0
        match_forms = ['om.', '-', '~', ' ', '']

        segment = {}
        segment_counter = 0

        offset = {}
        offset_counter = s.segmentConfig['segmentOffset']

        segment_index = 1

        logfile = s.dicerFolder + ms + '-words.log'
        with open(logfile, 'w+') as file:
            for addr in s.variantModel['addresses']:
                if addr.verse_num != cur_v:
                    if segment_counter > s.segmentConfig['segmentSize']:
                        segment['end_chapter'] = str(cur_c)
                        segment['end_verse'] = str(cur_v)
                        segment['index'] = segment_index
                        segment['label'] = segment['start_chapter'] + ',' + segment['start_verse'] + '-' + segment['end_chapter'] + ',' + segment['end_verse']
                        segment['address_count'] = len(segment['addresses'])
                        segment['word_count'] = segment_counter
                        s.dicer_segments.append(segment)

                        segment_index = segment_index + 1
                        segment_counter = 0
                        segment = {}

                    if offset_counter > s.segmentConfig['segmentSize']:
                        offset['end_chapter'] = str(cur_c)
                        offset['end_verse'] = str(cur_v)
                        offset['index'] = segment_index
                        offset['label'] = offset['start_chapter'] + ',' + offset['start_verse'] + '-' + offset['end_chapter'] + ',' + offset['end_verse']
                        offset['address_count'] = len(offset['addresses'])
                        offset['word_count'] = offset_counter

                        if len(s.dicer_segments) > 0:
                            if s.doOffsets:
                                s.dicer_segments.append(offset)
                                segment_index = segment_index + 1

                        offset_counter = 0
                        offset = {}

                    cur_v = addr.verse_num
                    v_count = v_count + 1

                if int(addr.chapter_num) != cur_c:
                    cur_c = int(addr.chapter_num)
                    c_count = c_count + 1

                if not segment.has_key('start_verse'):
                    segment['start_chapter'] = str(cur_c)
                    segment['start_verse'] = str(cur_v)
                    segment['addresses'] = []

                if not offset.has_key('start_verse'):
                    offset['start_chapter'] = str(cur_c)
                    offset['start_verse'] = str(cur_v)
                    offset['addresses'] = []

                tform = addr.getTextFormForMS(ms).strip()
                addr.reference_form = tform
                segment['addresses'].append(addr)
                offset['addresses'].append(addr)

                if tform not in match_forms:
                    file.write((tform + '\n').encode('UTF-8'))
                    w_count = w_count + 1
                    offset_counter = offset_counter + 1
                    segment_counter = segment_counter + 1

            if (segment_counter > s.segmentConfig['segmentMin']):
                segment['end_chapter'] = str(cur_c)
                segment['end_verse'] = str(cur_v)
                segment['index'] = segment_index
                segment['label'] = segment['start_chapter'] + ',' + segment['start_verse'] + '-' + segment['end_chapter'] + ',' + segment['end_verse']
                segment['address_count'] = len(segment['addresses'])
                segment['word_count'] = segment_counter
                s.dicer_segments.append(segment)
                segment_index = segment_index + 1
                segment_counter = 0

            # Extra segments
            extra_segments = c.get('extraSegments')
            range_data = c.get('rangeData')
            for rangeid in extra_segments:
                if not range_data.has_key(rangeid):
                    continue

                ranges = range_data[rangeid]

                segment = {}
                segment['index'] = segment_index
                segment['start_chapter'] = str(ranges[0]['chapter'])
                segment['start_verse'] = str(ranges[0]['startVerse'])
                segment['end_chapter'] = str(ranges[len(ranges) - 1]['chapter'])
                segment['end_verse'] = str(ranges[len(ranges) - 1]['endVerse'])
                segment['label'] = segment['start_chapter'] + ',' + segment['start_verse'] + '-' + segment['end_chapter'] + ',' + segment['end_verse']

                segment['addresses'] = []
                model = s.rangeMgr.getModel(rangeid)
                for addr in model['addresses']:
                    tform = addr.getTextFormForMS(ms).strip()
                    addr.reference_form = tform
                    segment['addresses'].append(addr)

                    if tform not in match_forms:
                        file.write((tform + '\n').encode('UTF-8'))
                        w_count = w_count + 1
                        segment_counter = segment_counter + 1

                segment['address_count'] = len(segment['addresses'])
                segment['word_count'] = segment_counter
                s.dicer_segments.append(segment)

                segment_index = segment_index + 1
                segment_counter = 0

            file.close()

        s.info('Saving dicer segments')

        segfile = s.dicerFolder + ms + '-segments.json'
        jdata = json.dumps(s.dicer_segments, cls=SegmentEncoder, ensure_ascii=False)
        with open(segfile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

        s.info('Saving word stats')
        w_stats = {}
        w_stats['chapter_count'] = c_count
        w_stats['verse_count'] = v_count
        w_stats['word_count'] = w_count
        w_stats['verses_per_chapter'] = v_count / c_count
        w_stats['words_per_chapter'] = w_count / c_count
        w_stats['words_per_verse'] = w_count / v_count

        statsfile = s.dicerFolder + ms + '-stats.json'
        jdata = json.dumps(w_stats, ensure_ascii=False)
        with open(statsfile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

    def runQCA(s, refMS):
        s.info('Generating QCA results')
        for segment in s.dicer_segments:
            segment['manuscripts'] = s.variantModel['manuscripts']

            tt = TruthTable()
            tt.initialize(segment['label'], [ refMS ], s.qcaSet, segment)
            tt.generate()

            # Initialize Python 3.6 environment
            py3_env = os.environ.copy()
            py3_env['PYTHONPATH'] = 'C:\Dev\Python36\Lib;'
            py3_env['PY_PYTHON'] = '3'
            py3_env['PATH'] = 'C:\Dev\python36;C:\Dev\python36\Scripts;'

            # TTMinimizer.py -v -f c01-05
            s.info('Calling TTMinimizer.py with', refMS)
            p = ['TTMinimizer.py']
            p.append('-v')
            p.append('-f')
            p.append(segment['label'] + '-' + refMS)
            p.append('-q')
            p.append(s.qcaSet)
            p.append('-S')
            p.append(s.statsFolder)
            proc = subprocess.Popen(p, env=py3_env, stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()

    c565 = [ '038', '565', '700']
    def isCluster565(s, greek_mss):
        scores = { 'affinity': 0.0, 'exclusivity': 0.0, 'combined': 0.0 }
        if not '038' in greek_mss and not '565' in greek_mss:
            return scores

        no_penalty_mss = [ '13', '69', '124', '346', '543', '788', '826', '828', '837', '983', '2542' ]

        c565_isect = set(greek_mss) & set(Dicer.c565)
        np_isect = set(greek_mss) & set(no_penalty_mss)
        others = len(greek_mss) - len(c565_isect) - len(np_isect)

        f03_isect = set(greek_mss) & set(Dicer.f03)
        if len(f03_isect) > 1:
            others = others - len(f03_isect) + 1

        f1_isect = set(greek_mss) & set(Dicer.f1)
        if len(f1_isect) > 1:
            others = others - len(f1_isect) + 1

        # f13 already in no penalty MSS!

        # 1 - 3 score, 3 highest
        affinity = 1
        if len(c565_isect) == 3:
            affinity = 3
        elif '038' in greek_mss and '565' in greek_mss:
            affinity = 2

        # 1 - 3 score, 3 highest
        exclusivity = 0
        if others <= 8: exclusivity = 1
        if others <= 5: exclusivity = 2
        if others <= 2: exclusivity = 3

        combined_score = (affinity + exclusivity) * 1.0 / 6  if exclusivity > 0.0 else 0.0
        combined_score_formatted = '%.2f' % round(combined_score, 2)
    
        scores['affinity'] = affinity
        scores['exclusivity'] = exclusivity
        scores['combined'] = combined_score
        scores['combined_formatted'] = combined_score_formatted
        scores['member_count'] = len(c565_isect)
        scores['nonmember_count'] = others

        return scores

    f03 = [ '01', '03', '019', '037', '33', '579', '892', '1342' ]
    def isFamily03(s, greek_mss):
        scores = { 'affinity': 0.0, 'exclusivity': 0.0, 'combined': 0.0 }
        if not '03' in greek_mss:
            return scores

        no_penalty_mss = [ '04', '044', '083', '0274' ]

        f03_isect = set(greek_mss) & set(Dicer.f03)
        if len(f03_isect) < 3:
            return scores

        np_isect = set(greek_mss) & set(no_penalty_mss)
        others = len(greek_mss) - len(f03_isect) - len(np_isect)

        c565_isect = set(greek_mss) & set(Dicer.c565)
        if len(c565_isect) > 1:
            others = others - len(c565_isect) + 1

        f1_isect = set(greek_mss) & set(Dicer.f1)
        if len(f1_isect) > 1:
            others = others - len(f1_isect) + 1

        f13_isect = set(greek_mss) & set(Dicer.f13)
        if len(f13_isect) > 1:
            others = others - len(f13_isect) + 1

        # 1 - 5 score, 5 highest
        affinity = len(f03_isect) - 2 if len(f03_isect) > 2 else 0
        if len(f03_isect) > 6:
            affinity = 5

        # 1 - 5 score, 5 highest
        exclusivity = 0
        if others <= 8: exclusivity = 1
        if others <= 5: exclusivity = 2
        if others <= 3: exclusivity = 3
        if others <= 2: exclusivity = 4
        if others <= 1: exclusivity = 5

        combined_score = (affinity + exclusivity) * 1.0 / 10 if exclusivity > 0.0 else 0.0
        combined_score_formatted = '%.2f' % round(combined_score, 2)

        scores['affinity'] = affinity
        scores['exclusivity'] = exclusivity
        scores['combined'] = combined_score
        scores['combined_formatted'] = combined_score_formatted
        scores['member_count'] = len(f03_isect)
        scores['nonmember_count'] = others

        return scores

    f1 = [ '1', '1582', '118', '131', '191', '205', '209', '872', '1273', '2193' ]
    def isFamily1(s, greek_mss):
        scores = { 'affinity': 0.0, 'exclusivity': 0.0, 'combined': 0.0 }
        if not set([ '1', '1582' ]) in set(greek_mss):
            return scores

        no_penalty_mss = [ '22', '251', '697', '791', '1005', '1278', '1365', '2372' ]
        f1_isect = set(greek_mss) & set(Dicer.f1)
        np_isect = set(greek_mss) & set(no_penalty_mss)
        others = len(greek_mss) - len(f1_isect) - len(np_isect)

        c565_isect = set(greek_mss) & set(Dicer.c565)
        if len(c565_isect) > 1:
            others = others - len(c565_isect) + 1

        f03_isect = set(greek_mss) & set(Dicer.f03)
        if len(f03_isect) > 1:
            others = others - len(f03_isect) + 1

        f13_isect = set(greek_mss) & set(Dicer.f13)
        if len(f13_isect) > 1:
            others = others - len(f13_isect) + 1

        # 1 - 5 score, 5 highest
        affinity = len(f1_isect) - 1 if len(f1_isect) > 1 else 0
        if len(f1_isect) > 5:
            affinity = 5

        # 1 - 5 score, 5 highest
        exclusivity = 0
        if others <= 8: exclusivity = 1
        if others <= 5: exclusivity = 2
        if others <= 3: exclusivity = 3
        if others <= 2: exclusivity = 4
        if others <= 1: exclusivity = 5

        combined_score = (affinity + exclusivity) * 1.0 / 10 if exclusivity > 0.0 else 0.0
        combined_score_formatted = '%.2f' % round(combined_score, 2)

        scores['affinity'] = affinity
        scores['exclusivity'] = exclusivity
        scores['combined'] = combined_score
        scores['combined_formatted'] = combined_score_formatted
        scores['member_count'] = len(f1_isect)
        scores['nonmember_count'] = others

        return scores

    f13 = [ '13', '69', '124', '346', '543', '788', '826', '828', '983' ]
    def isFamily13(s, greek_mss):
        scores = { 'affinity': 0.0, 'exclusivity': 0.0, 'combined': 0.0 }

        no_penalty_mss = [ '837' ]
        f13_isect = set(greek_mss) & set(Dicer.f13)
        if len(f13_isect) < 3:
            return scores

        np_isect = set(greek_mss) & set(no_penalty_mss)
        others = len(greek_mss) - len(f13_isect) - len(np_isect)

        c565_isect = set(greek_mss) & set(Dicer.c565)
        if len(c565_isect) > 1:
            others = others - len(c565_isect) + 1

        f03_isect = set(greek_mss) & set(Dicer.f03)
        if len(f03_isect) > 1:
            others = others - len(f03_isect) + 1

        f1_isect = set(greek_mss) & set(Dicer.f1)
        if len(f1_isect) > 1:
            others = others - len(f1_isect) + 1

        # 1 - 5 score, 5 highest
        affinity = len(f13_isect) - 2 if len(f13_isect) > 2 else 0
        if len(f13_isect) > 6:
            affinity = 5

        # 1 - 5 score, 5 highest
        exclusivity = 0
        if others <= 8: exclusivity = 1
        if others <= 5: exclusivity = 2
        if others <= 3: exclusivity = 3
        if others <= 2: exclusivity = 4
        if others <= 1: exclusivity = 5

        combined_score = (affinity + exclusivity) * 1.0 / 10 if exclusivity > 0.0 else 0.0
        combined_score_formatted = '%.2f' % round(combined_score, 2)

        scores['affinity'] = affinity
        scores['exclusivity'] = exclusivity
        scores['combined'] = combined_score
        scores['combined_formatted'] = combined_score_formatted
        scores['member_count'] = len(f13_isect)
        scores['nonmember_count'] = others

        return scores

    def groupApparatus(s, greek_mss, latin_mss):
        c565 = set(greek_mss) & set(Dicer.c565)
        greek_mss = set(greek_mss) - c565

        f03 = set(greek_mss) & set(Dicer.f03)
        greek_mss = set(greek_mss) - f03

        f1 = set(greek_mss) & set(Dicer.f1)
        greek_mss = set(greek_mss) - f1

        f13 = set(greek_mss) & set(Dicer.f13)
        greek_mss = set(greek_mss) - f13

        greek_mss = sorted(list(greek_mss), cmp=sortMSS)
        apparatus = ' '.join(greek_mss)

        if len(c565):
            c565_list = sorted(list(c565), cmp=sortMSS)
            apparatus = apparatus + ' c(' + ' '.join(c565_list) + ')'

        if len(f03):
            f03_list = sorted(list(f03), cmp=sortMSS)
            apparatus = apparatus + ' f(' + ' '.join(f03_list) + ')'

        if len(f1):
            f1_list = sorted(list(f1), cmp=sortMSS)
            apparatus = apparatus + ' f(' + ' '.join(f1_list) + ')'

        if len(f13):
            f13_list = sorted(list(f13), cmp=sortMSS)
            apparatus = apparatus + ' f(' + ' '.join(f13_list) + ')'

        if (len(latin_mss)):
            apparatus = apparatus + ' L(' + ' '.join(latin_mss) + ')'

        return apparatus

    def initCorrector(s):
        return { 'readings': [], 'count': 0, 'prev_count': 0, 'count_delta': 0, 'count_delta_pc': 0.0, 'freq': 0, 'freq_delta': 0 }

    def isDistinctive(s, refMS, vu, reading, group):
        c = s.config
        if not reading or vu.isReferenceSingular(refMS) or reading.hasManuscript('35'):
            return False

        g_counts = {}
        msGroupAssignments = c.get('msGroupAssignments')
        nonref_count = reading.countNonRefGreekManuscriptsByGroup(refMS, msGroupAssignments, g_counts)

        if nonref_count == 0:
            return False

        base_mss = []
        base_mss.append('28')
        base_mss.append('2542')
        for ms, gp in msGroupAssignments.iteritems():
            if gp in Dicer.CORE_GROUPS and gp != group['name']:
                base_mss.append(ms)

        if set(base_mss) & set(reading.manuscripts):
            return False

        member_count = 0
        for ms in group['members']:
            if reading.hasManuscript(ms):
                member_count = member_count + 1

        if member_count < group['minOccurs']:
            return False

        return True

    def prepareHauptlisten(s, refMS):
        c = s.config
        for segment in s.dicer_segments:
            s.info('Generating Hauptliste for', segment['label'])

            if not segment.has_key('ref_data'):
                segment['ref_data'] = {}

            if not segment.has_key('ms_refs_d'):
                segment['ms_refs_d'] = {}

            ref_data = {}
            ref_data['majority_count'] = 0

            ref_data['nonM_instances'] = {}
            ref_data['D_instances'] = {}
            ref_data['L_instances'] = {}

            ref_data['nonM_lac'] = {}
            ref_data['D_lac'] = {}
            ref_data['L_lac'] = {}

            ref_data['nonM_readings'] = []
            ref_data['D_readings'] = []
            ref_data['L_readings'] = []
            ref_data['S_readings'] = []

            ref_data['correctors'] = {}
            for corrector in Util.SINAI_HANDS:
                if corrector == '01*':
                    continue
                ref_data['correctors']['01' + corrector] = s.initCorrector()
            for corrector in Util.BEZAE_HANDS:
                if corrector == '05*':
                    continue
                ref_data['correctors']['05' + corrector] = s.initCorrector()

            for addr in segment['addresses']:
                for vu in addr.variation_units:
                    s.vu_count = s.vu_count + 1
                    if not vu.hasRetroversion:
                        s.no_retro_count = s.no_retro_count + 1

                    if not vu.startingAddress:
                        vu.startingAddress = addr

                    reading_info = {}
                    reading_info['variant_label'] = vu.label
                    reading_info['verse_reference'] = str(addr.chapter_num) + ':' + str(addr.verse_num)

                    # Correctors
                    for reading in vu.readings:
                        for corrector in reading.sinai_correctors:
                            r_info = {}
                            r_info['display_value'] = reading.getDisplayValue()
                            r_info['variant_label'] = vu.label
                            r_info['verse_reference'] = str(addr.chapter_num) + ':' + str(addr.verse_num)
                            ref_data['correctors']['01' + corrector]['readings'].append(r_info)
                        for corrector in reading.bezae_correctors:
                            r_info = {}
                            r_info['display_value'] = reading.getDisplayValue()
                            r_info['variant_label'] = vu.label
                            r_info['verse_reference'] = str(addr.chapter_num) + ':' + str(addr.verse_num)
                            ref_data['correctors']['05' + corrector]['readings'].append(r_info)

                    r_reading = vu.getReadingForManuscript(refMS)
                    if not r_reading:
                        s.na_readings.append(vu.label)
                        continue

                    if vu.isReferenceSingular(refMS):
                        ref_data['S_readings'].append(reading_info)
                        s.s_readings.append(vu.label)
                        if len(r_reading.manuscripts) == 1 and vu.hasRetroversion:
                            s.s_05_retro_readings.append(vu.label)
                        elif len(r_reading.manuscripts) == 2 and vu.hasRetroversion:
                            s.s_05VL5_readings.append(vu.label)
                        continue
                    elif refMS == '05' and isSubSingular(s.subsingular, vu, refMS):
                        ref_data['S_readings'].append(reading_info)
                        s.s_readings.append(vu.label)
                        continue

                    m_reading = vu.getReadingForManuscript('35')
                    if '35' in r_reading.manuscripts:
                        ref_data['majority_count'] = ref_data['majority_count'] + 1
                        s.m_readings.append(vu.label)
                        if vu.isSingular():
                            s.m_sg_readings.append(vu.label)
                        continue

                    reading_info['mss'] = []
                    reading_info['reading_value'] = r_reading.getDisplayValue()
                    latin_mss = []
                    greek_mss = []

                    # Determine layer
                    for ms in r_reading.manuscripts:
                        if ms == refMS:
                            continue

                        if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
                            if ms[:2] == 'VL': ms = ms[2:]
                            latin_mss.append(ms)
                        else:
                            greek_mss.append(ms)

                    greek_mss = sorted(greek_mss, cmp=sortMSS)

                    reading_info['greek_mss_count'] = len(greek_mss)
                    reading_info['latin_mss_count'] = len(latin_mss)
                    reading_info['greek_apparatus'] = ' '.join(greek_mss)
                    reading_info['latin_apparatus'] = ' '.join(latin_mss)
                    reading_info['grouped_apparatus'] = s.groupApparatus(greek_mss, latin_mss)

                    # Layer
                    layer = computeLayer(s.latinLayerCore, s.latinLayerMulti, refMS, vu.label, r_reading)
                    if layer == 'L':
                        reading_info['L_layer'] = True
                        reading_info['D_layer'] = False
                        s.l_readings.append(vu.label)
                    else:
                        reading_info['L_layer'] = False
                        reading_info['D_layer'] = True
                        s.d_readings.append(vu.label)

                    if reading_info['L_layer']:
                        ref_data['L_readings'].append(reading_info)
                    elif reading_info['D_layer']:
                        ref_data['D_readings'].append(reading_info)
                    ref_data['nonM_readings'].append(reading_info)

                    # MS refs in D
                    if reading_info['D_layer']:
                        for ms in r_reading.manuscripts:
                            if ms == refMS:
                                continue
                            if not segment['ms_refs_d'].has_key(ms):
                                segment['ms_refs_d'][ms] = []
                            segment['ms_refs_d'][ms].append(vu.label)

                    # Family profile scores
                    reading_info['c565_scores'] = s.isCluster565(greek_mss)
                    reading_info['f03_scores'] = s.isFamily03(greek_mss)
                    reading_info['f1_scores'] = s.isFamily1(greek_mss)
                    reading_info['f13_scores'] = s.isFamily13(greek_mss)

                    # Process core groups
                    core_groups = c.get('coreGroups')
                    for gp in core_groups:
                        if not gp['name'] in Dicer.CORE_GROUPS:
                            continue

                        if not s.isDistinctive(refMS, vu, r_reading, gp):
                            continue

                        if not reading_info.has_key('core_groups'):
                            reading_info['core_groups'] = []
                        reading_info['core_groups'].append(gp['name'])

                        gp_instance = {}
                        gp_instance['variant_label'] = vu.label
                        gp_instance['reading_value'] = r_reading.getDisplayValue()
                        gp_instance['verse_reference'] = str(addr.chapter_num) + ':' + str(addr.verse_num)

                        if reading_info['D_layer']:
                            if not ref_data.has_key('D_group_instances'):
                                ref_data['D_group_instances'] = {}
                            if not ref_data['D_group_instances'].has_key(gp['name']):
                                ref_data['D_group_instances'][gp['name']] = []
                            ref_data['D_group_instances'][gp['name']].append(gp_instance)

                    # Process MSS
                    for ms in s.variantModel['manuscripts']:
                        if ms == refMS or ms == '35':
                            continue

                        # Is ms attested at this variant?
                        rdg = vu.getReadingForManuscript(ms)
                        if not rdg:
                            if not ref_data['nonM_lac'].has_key(ms):
                                ref_data['nonM_lac'][ms] = []
                            ref_data['nonM_lac'][ms].append(vu.label)
                            if reading_info['L_layer']:
                                if not ref_data['L_lac'].has_key(ms):
                                    ref_data['L_lac'][ms] = []
                                ref_data['L_lac'][ms].append(vu.label)
                            elif reading_info['D_layer']:
                                if not ref_data['D_lac'].has_key(ms):
                                    ref_data['D_lac'][ms] = []
                                ref_data['D_lac'][ms].append(vu.label)
                            continue

                        # Does ms support present reading?
                        if not r_reading.hasManuscript(ms):
                            continue

                        # Add MS to supporting witnesses
                        reading_info['mss'].append(ms)

                        ms_instance = {}
                        ms_instance['variant_label'] = vu.label
                        ms_instance['reading_value'] = r_reading.getDisplayValue()

                        if not ref_data['nonM_instances'].has_key(ms):
                            ref_data['nonM_instances'][ms] = []
                        ref_data['nonM_instances'][ms].append(ms_instance)

                        if reading_info['L_layer']:
                            if not ref_data['L_instances'].has_key(ms):
                                ref_data['L_instances'][ms] = []
                            ref_data['L_instances'][ms].append(ms_instance)
                        elif reading_info['D_layer']:
                            if not ref_data['D_instances'].has_key(ms):
                                ref_data['D_instances'][ms] = []
                            ref_data['D_instances'][ms].append(ms_instance)

            segment['ref_data'][refMS] = ref_data

    def getMS(s, j_seg, ms):
        m_list = []
        if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
            m_list = j_seg['latin_mss']
        else:
            m_list = j_seg['greek_mss']

        for msdat in m_list:
            if msdat['manuscript'] == ms:
                return msdat

        return None

    def vuReferenceList(s, infos):
        labels = []
        for info in infos:
            labels.append(info['verse_reference'])
        return labels

    def vuLabelString(s, infos):
        labels = ''
        for info in infos:
            if labels:
                labels = labels + ', '
            labels = labels + info['variant_label']
        return labels

    def computeHauptlisten(s, refMS):
        c = s.config

        ref_settings = c.get('hauptlisteDisplay')[refMS]
        bchart_ref_mss = ref_settings['bchart_ref_mss']
        lchart_ref_mss = ref_settings['lchart_ref_mss']
        lchart_ref_layers = [ 'M', 'D', 'L' ]

        bar_values = {} # for bar charts
        line_ms_pc_values = {} # for MS line charts
        line_ms_delta_values = {} # for MS line charts (deltas)
        line_la_freq_values = {} # for layer line charts
        line_la_delta_values = {} # for layer line charts (deltas)
        line_la_counts = {} # for layer horizontal bar chart
        segment_labels = [] # for line charts

        # list of rows for HL CSV
        hauptliste_matrix = []
        hdr = ['']
        for ms in s.variantModel['manuscripts']:
            if ms == refMS: continue
            hdr.append(ms)
        hauptliste_matrix.append(hdr) # hdr row

        # list of rows for SO CSV
        unions = c.get('unions')
        intersections = c.get('intersections')
        exclusions = c.get('exclusions')
        setop_matrix = []
        hdr = ['']
        for union in unions:
            u_str = ' U '.join(union)
            hdr.append(u_str)
        for isect in intersections:
            u_str1 = '(' + ' U '.join(isect[0]) + ')'
            u_str2 = '(' + ' U '.join(isect[1]) + ')'
            hdr.append(u_str1 + ' x ' + u_str2)
        for exclu in exclusions:
            u_str1 = '(' + ' U '.join(exclu[0]) + ')'
            u_str2 = '(' + ' U '.join(exclu[1]) + ')'
            hdr.append(u_str1 + ' - ' + u_str2)
        setop_matrix.append(hdr) # hdr row

        hauptliste_delta_matrix = []
        hdr = ['']
        for ms in s.variantModel['manuscripts']:
            if ms == refMS: continue
            hdr.append(ms)
        hauptliste_delta_matrix.append(hdr) # hdr row

        hauptliste = {}
        hauptliste['segments'] = []
        hauptliste['ref_ms'] = refMS
        mcount_prev = 0
        nmcount_prev = 0
        dcount_prev = 0
        lcount_prev = 0
        scount_prev = 0
        mfreq_prev = 0.0
        nmfreq_prev = 0.0
        dfreq_prev = 0.0
        lfreq_prev = 0.0
        sfreq_prev = 0.0
        seg_prev = {}
        hauptliste_matrix_row = []
        hauptliste_delta_matrix_row = []
        setop_matrix_row = []
        last_word_count_multiplier = 0.0

        c_prev_count = {}
        for corrector in Util.SINAI_HANDS:
            if corrector == '01*':
                continue
            c_prev_count['01' + corrector] = 0
        for corrector in Util.BEZAE_HANDS:
            if corrector == '05*':
                continue
            c_prev_count['05' + corrector] = 0

        c_prev_freq = {}
        for corrector in Util.SINAI_HANDS:
            if corrector == '01*':
                continue
            c_prev_freq['01' + corrector] = 0.0
        for corrector in Util.BEZAE_HANDS:
            if corrector == '05*':
                continue
            c_prev_freq['05' + corrector] = 0.0

        cfile = s.dicerFolder + refMS + '-' + s.segmentConfig['label'] + '-segment-L-counts.csv'
        with open(cfile, 'w+') as file:
            file.write('Position\tSegment\tWords\tS Readings\tL Readings\tG Readings\tM Readings\n')
            file.close()
        for sidx, segment in enumerate(s.dicer_segments):
            ref_data = segment['ref_data'][refMS]

            segment_labels.append(segment['label'])
            hauptliste_matrix_row.append(segment['label'])
            hauptliste_delta_matrix_row.append(segment['label'])
            setop_matrix_row.append(segment['label'])

            majority_count = ref_data['majority_count']
            majority_count_prev = mcount_prev
            majority_count_delta = majority_count - mcount_prev
            majority_count_delta_pc = round(majority_count * 1.0 / majority_count_prev if majority_count_prev != 0 else 0.0, 3)
            majority_freq = segment['word_count'] * 1.0 / ref_data['majority_count']
            majority_freq = round(majority_freq, 1)
            mfreq_delta = mfreq_prev / majority_freq if majority_freq > 0 else 0.0
            mfreq_delta = round(mfreq_delta, 3)
            mcount_prev = majority_count
            mfreq_prev = majority_freq

            nonM_count = len(ref_data['nonM_readings'])
            nonM_count_prev = nmcount_prev
            nonM_count_delta = nonM_count - nmcount_prev
            nonM_count_delta_pc = round(nonM_count * 1.0 / nonM_count_prev if nonM_count_prev != 0 else 0.0, 3)
            nonmajority_freq = segment['word_count'] * 1.0 / len(ref_data['nonM_readings']) if len(ref_data['nonM_readings']) > 0 else 0.0
            nonmajority_freq = round(nonmajority_freq, 1)
            nmfreq_delta = nmfreq_prev / nonmajority_freq if nonmajority_freq > 0 else 0.0
            nmfreq_delta = round(nmfreq_delta, 3)
            nmcount_prev = nonM_count
            nmfreq_prev = nonmajority_freq

            D_count = len(ref_data['D_readings'])
            D_count_prev = dcount_prev
            D_count_delta = D_count - dcount_prev
            D_count_delta_pc = round(D_count * 1.0 / D_count_prev if D_count_prev != 0 else 0.0, 3)
            D_freq = segment['word_count'] * 1.0 / len(ref_data['D_readings']) if len(ref_data['D_readings']) > 0 else 0.0
            D_freq = round(D_freq, 1)
            dfreq_delta = dfreq_prev / D_freq if D_freq > 0 else 0.0
            dfreq_delta = round(dfreq_delta, 3)
            dcount_prev = D_count
            dfreq_prev = D_freq

            L_count = len(ref_data['L_readings'])
            L_count_prev = lcount_prev
            L_count_delta = L_count - lcount_prev
            L_count_delta_pc = round(L_count * 1.0 / L_count_prev if L_count_prev != 0 else 0.0, 3)
            L_freq = segment['word_count'] * 1.0 / len(ref_data['L_readings']) if len(ref_data['L_readings']) > 0 else 0.0
            L_freq = round(L_freq, 1)
            lfreq_delta = lfreq_prev / L_freq if L_freq > 0 else 0.0
            lfreq_delta = round(lfreq_delta, 3)
            lcount_prev = L_count
            lfreq_prev = L_freq

            S_count = len(ref_data['S_readings'])
            S_count_prev = scount_prev
            S_count_delta = S_count - scount_prev
            S_count_delta_pc = round(S_count * 1.0 / S_count_prev if S_count_prev != 0 else 0.0, 3)
            S_freq = segment['word_count'] * 1.0 / len(ref_data['S_readings']) if len(ref_data['S_readings']) > 0 else 0.0
            S_freq = round(S_freq, 1)
            sfreq_delta = sfreq_prev / S_freq if S_freq > 0 else 0.0
            sfreq_delta = round(sfreq_delta, 3)
            scount_prev = S_count
            sfreq_prev = S_freq

            for name, cor_info in ref_data['correctors'].iteritems():
                cor_info['count'] = len(cor_info['readings'])
                cor_info['prev_count'] = c_prev_count[name]
                cor_info['count_delta'] = cor_info['count'] - cor_info['prev_count']
                cor_info['count_delta_pc'] = round(cor_info['count'] * 1.0 / cor_info['prev_count'] if cor_info['prev_count'] != 0 else 0.0, 3)
                c_freq = round(segment['word_count'] * 1.0 / cor_info['count'] if cor_info['count'] > 0 else 0.0, 1)
                cor_info['freq'] = c_freq
                c_delta = round(c_prev_freq[name] / c_freq if c_freq > 0 else 0.0, 3)  
                cor_info['freq_delta'] = c_delta
                cor_info['labels'] = refListToString(s.vuReferenceList(cor_info['readings']))
                c_prev_freq[name] = c_freq
                c_prev_count[name] = cor_info['count']

            with open(cfile, 'a+') as file:
                file.write(str(sidx + 1) + '\t' + segment['label'] + '\t' + str(segment['word_count']) + '\t' + str(len(ref_data['S_readings'])) + '\t' + str(len(ref_data['L_readings'])) + '\t' + str(len(ref_data['D_readings'])) + '\t' + str(ref_data['majority_count']) + '\n')
                file.close()

            multiplier_factor = s.segmentConfig['segmentSize'] + 10

            j_segment = {}
            j_segment['majority_count'] = majority_count
            j_segment['majority_count_prev'] = majority_count_prev
            j_segment['majority_count_delta'] = majority_count_delta
            j_segment['majority_count_delta_pc'] = majority_count_delta_pc
            j_segment['majority_freq'] = majority_freq
            j_segment['majority_freq_delta'] = mfreq_delta
            j_segment['nonM_count'] = nonM_count
            j_segment['nonM_count_prev'] = nonM_count_prev
            j_segment['nonM_count_delta'] = nonM_count_delta
            j_segment['nonM_count_delta_pc'] = nonM_count_delta_pc
            j_segment['nonM_freq'] = nonmajority_freq
            j_segment['nonM_freq_delta'] = nmfreq_delta
            j_segment['D_count'] = D_count
            j_segment['D_count_prev'] = D_count_prev
            j_segment['D_count_delta'] = D_count_delta
            j_segment['D_count_delta_pc'] = D_count_delta_pc
            j_segment['D_freq'] = D_freq
            j_segment['D_freq_delta'] = dfreq_delta
            j_segment['D_labels'] = refListToString(s.vuReferenceList(ref_data['D_readings']))
            j_segment['L_count'] = L_count
            j_segment['L_count_prev'] = L_count_prev
            j_segment['L_count_delta'] = L_count_delta
            j_segment['L_count_delta_pc'] = L_count_delta_pc
            j_segment['L_freq'] = L_freq
            j_segment['L_freq_delta'] = lfreq_delta
            j_segment['L_labels'] = refListToString(s.vuReferenceList(ref_data['L_readings']))
            j_segment['S_count'] = S_count
            j_segment['S_count_prev'] = S_count_prev
            j_segment['S_count_delta'] = S_count_delta
            j_segment['S_count_delta_pc'] = S_count_delta_pc
            j_segment['S_freq'] = S_freq
            j_segment['S_freq_delta'] = sfreq_delta
            j_segment['S_labels'] = refListToString(s.vuReferenceList(ref_data['S_readings']))
            j_segment['index'] = segment['index']
            j_segment['address_count'] = segment['address_count']
            j_segment['word_count'] = segment['word_count']
            j_segment['word_count_multiplier'] = multiplier_factor * 1.0 / segment['word_count']
            j_segment['last_word_count_multiplier'] = last_word_count_multiplier
            j_segment['label'] = segment['label']
            j_segment['greek_mss'] = []
            j_segment['latin_mss'] = []
            j_segment['D_readings'] = []
            j_segment['L_readings'] = []
            j_segment['correctors'] = ref_data['correctors']
            last_word_count_multiplier = j_segment['word_count_multiplier']

            j_profiles = {}
            j_profiles['f03_readings'] = []
            j_profiles['f1_readings'] = []
            j_profiles['f13_readings'] = []
            j_profiles['c565_readings'] = []
            j_profiles['032_readings'] = []

            # Layer count horizontal bar chart
            if not line_la_counts.has_key('M'):
                line_la_counts['M'] = []
            line_la_counts['M'].append(ref_data['majority_count'])
            if not line_la_counts.has_key('D'):
                line_la_counts['D'] = []
            line_la_counts['D'].append(len(ref_data['D_readings']))
            if not line_la_counts.has_key('L'):
                line_la_counts['L'] = []
            line_la_counts['L'].append(len(ref_data['L_readings']))
            if not line_la_counts.has_key('S'):
                line_la_counts['S'] = []
            line_la_counts['S'].append(len(ref_data['S_readings']))

            # Layer frequency line charts
            if not line_la_freq_values.has_key('M'):
                line_la_freq_values['M'] = []
            line_la_freq_values['M'].append(majority_freq)
            if not line_la_freq_values.has_key('D'):
                line_la_freq_values['D'] = []
            line_la_freq_values['D'].append(D_freq)
            if not line_la_freq_values.has_key('L'):
                line_la_freq_values['L'] = []
            line_la_freq_values['L'].append(L_freq)

            # Layer delta line charts
            if not line_la_delta_values.has_key('M'):
                line_la_delta_values['M'] = []
            line_la_delta_values['M'].append(mfreq_delta)
            if not line_la_delta_values.has_key('D'):
                line_la_delta_values['D'] = []
            line_la_delta_values['D'].append(dfreq_delta)
            if not line_la_delta_values.has_key('L'):
                line_la_delta_values['L'] = []
            line_la_delta_values['L'].append(lfreq_delta)

            for reading in ref_data['nonM_readings']:
                j_reading = {}
                j_reading['variant_label'] = reading['variant_label']
                j_reading['reading_value'] = reading['reading_value']
                j_reading['greek_mss_count'] = reading['greek_mss_count']
                j_reading['latin_mss_count'] = reading['latin_mss_count']
                j_reading['greek_apparatus'] = reading['greek_apparatus']
                j_reading['latin_apparatus'] = reading['latin_apparatus']
                j_reading['grouped_apparatus'] = reading['grouped_apparatus']

                j_profile_scores = {}
                if reading['c565_scores']['combined'] > 0.5:
                    j_profile_scores['c565_scores'] = reading['c565_scores']
                    j_profiles['c565_readings'].append(j_reading)

                if reading['f03_scores']['combined'] > 0.5:
                    j_profile_scores['f03_scores'] = reading['f03_scores']
                    j_profiles['f03_readings'].append(j_reading)

                if reading['f1_scores']['combined'] > 0.5:
                    j_profile_scores['f1_scores'] = reading['f1_scores']
                    j_profiles['f1_readings'].append(j_reading)

                if reading['f13_scores']['combined'] > 0.5:
                    j_profile_scores['f13_scores'] = reading['f13_scores']
                    j_profiles['f13_readings'].append(j_reading)

                j_reading['profile_scores'] = j_profile_scores

                if reading['D_layer']:
                    j_segment['D_readings'].append(j_reading)
                if reading['L_layer']:
                    j_segment['L_readings'].append(j_reading)

            j_segment['profiles'] = j_profiles

            # Process unions
            for union in unions:
                union_refs = set()
                for ms in union:
                    if not segment['ms_refs_d'].has_key(ms):
                        continue
                    union_refs = union_refs | set(segment['ms_refs_d'][ms])
                ratio = str(round(len(union_refs) * 1.0 / D_count, 3))
                setop_matrix_row.append(ratio)

            # Process intersections
            for isect in intersections:
                u1_refs = set()
                u2_refs = set()
                u1 = isect[0]
                u2 = isect[1]
                for ms in u1:
                    if not segment['ms_refs_d'].has_key(ms):
                        continue
                    u1_refs = u1_refs | set(segment['ms_refs_d'][ms])
                for ms in u2:
                    if not segment['ms_refs_d'].has_key(ms):
                        continue
                    u2_refs = u2_refs | set(segment['ms_refs_d'][ms])
                isect_refs = u1_refs & u2_refs
                ratio = str(round(len(isect_refs) * 1.0 / D_count, 3))
                setop_matrix_row.append(ratio)

            # Process exclusions
            for exclu in exclusions:
                u1_refs = set()
                u2_refs = set()
                u1 = exclu[0]
                u2 = exclu[1]
                for ms in u1:
                    if not segment['ms_refs_d'].has_key(ms):
                        continue
                    u1_refs = u1_refs | set(segment['ms_refs_d'][ms])
                for ms in u2:
                    if not segment['ms_refs_d'].has_key(ms):
                        continue
                    u2_refs = u2_refs | set(segment['ms_refs_d'][ms])
                exclu_refs = u1_refs - u2_refs
                ratio = str(round(len(exclu_refs) * 1.0 / D_count, 3))
                setop_matrix_row.append(ratio)

            # Process core groups
            core_groups = c.get('coreGroups')
            for gp in core_groups:
                if not gp['name'] in Dicer.CORE_GROUPS:
                    continue

                g_name = gp['name']

                gpdat = {}
                gpdat['group'] = g_name

                if not ref_data.has_key('D_group_instances'):
                    ref_data['D_group_instances'] = {}

                gpdat['D_group_count'] = len(ref_data['D_group_instances'][g_name]) if ref_data['D_group_instances'].has_key(g_name) else 0
                gpdat['D_group_pc'] = round(gpdat['D_group_count'] * 1.0 / j_segment['D_count'] if j_segment['D_count'] != 0 else 0.0, 3)

                gpdat_prev = None
                if seg_prev:
                    gpdat_prev = seg_prev['group_data'][g_name] if seg_prev['group_data'].has_key(g_name) else None
                gpdat['D_group_count_prev'] = gpdat_prev['D_group_count'] if gpdat_prev else 0
                gpdat['D_group_count_delta'] = gpdat['D_group_count'] - gpdat['D_group_count_prev']
                gpdat['D_group_count_delta_pc'] = round(gpdat['D_group_count'] * 1.0 / gpdat['D_group_count_prev'] if gpdat['D_group_count_prev'] != 0 else 0.0, 3)

                gpdat['labels'] = ''
                if ref_data['D_group_instances'].has_key(g_name):
                    gpdat['labels'] = refListToString(s.vuReferenceList(ref_data['D_group_instances'][g_name]))

                if not j_segment.has_key('group_data'):
                    j_segment['group_data'] = {}
                j_segment['group_data'][g_name] = gpdat

            for ms in s.variantModel['manuscripts']:
                if ms == refMS:
                    continue

                msdat = {}
                msdat['manuscript'] = ms

                msdat['L_instance_count'] = 0
                if ref_data['L_instances'].has_key(ms):
                    msdat['L_instance_count'] = len(ref_data['L_instances'][ms])

                msdat['L_lac_count'] = 0
                if ref_data['L_lac'].has_key(ms):
                    msdat['L_lac_count'] = len(ref_data['L_lac'][ms])

                msdat['L_count'] = j_segment['L_count'] - msdat['L_lac_count']

                ratio_prev = 0.0
                if len(seg_prev):
                    msdat_prev = s.getMS(seg_prev, ms)
                    ratio_prev = msdat_prev['L_ratio'] if msdat_prev else 0.0

                ratio = 0.0
                if msdat['L_count']:
                    ratio = msdat['L_instance_count'] * 1.0 / msdat['L_count']
                    ratio = round(ratio, 3)
                msdat['L_ratio'] = ratio
                msdat['L_ratio_prev'] = ratio_prev
                msdat['L_ratio_delta'] = round(ratio - ratio_prev, 3)

                msdat['D_instance_count'] = 0
                if ref_data['D_instances'].has_key(ms):
                    msdat['D_instance_count'] = len(ref_data['D_instances'][ms])

                msdat['D_lac_count'] = 0
                if ref_data['D_lac'].has_key(ms):
                    msdat['D_lac_count'] = len(ref_data['D_lac'][ms])

                msdat['D_count'] = j_segment['D_count'] - msdat['D_lac_count']

                ratio_prev = 0.0
                if len(seg_prev):
                    msdat_prev = s.getMS(seg_prev, ms)
                    ratio_prev = msdat_prev['D_ratio'] if msdat_prev else 0.0

                ratio = 0.0
                inst_percent = 0.0
                if msdat['D_count']:
                    ratio = msdat['D_instance_count'] * 1.0 / msdat['D_count']
                    inst_percent = int(round(ratio * 100, 0))
                    ratio = round(ratio, 3)
                msdat['D_ratio'] = ratio
                msdat['D_ratio_prev'] = ratio_prev
                msdat['D_ratio_delta'] = round(ratio - ratio_prev, 3)
                inst_delta = int(round(msdat['D_ratio_delta'] * 100, 0))

                hauptliste_matrix_row.append('%.3f' % ratio)
                hauptliste_delta_matrix_row.append('%.3f' % msdat['D_ratio_delta'])

                if ms in bchart_ref_mss: # for charts
                    bar_values[ms] = inst_percent

                if ms in lchart_ref_mss:
                    # MS percent line charts
                    if not line_ms_pc_values.has_key(ms):
                        line_ms_pc_values[ms] = []
                    line_ms_pc_values[ms].append(inst_percent)

                    # MS delta line charts
                    if not line_ms_delta_values.has_key(ms):
                        line_ms_delta_values[ms] = []
                    line_ms_delta_values[ms].append(inst_delta)

                if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
                    j_segment['latin_mss'].append(msdat)
                else:
                    j_segment['greek_mss'].append(msdat)

            bardata = []
            for ms_key in bchart_ref_mss:
                bardata.append(bar_values[ms_key])
            j_segment['bar_data'] = bardata

            j_segment['greek_mss'] = sorted(j_segment['greek_mss'], cmp=sortHauptlisteD)[:30]
            j_segment['latin_mss'] = sorted(j_segment['latin_mss'], cmp=sortHauptlisteD)[:10]
            j_segment['greek_mss_Lsort'] = sorted(j_segment['greek_mss'], cmp=sortHauptlisteL)[:10]
            j_segment['latin_mss_Lsort'] = sorted(j_segment['latin_mss'], cmp=sortHauptlisteL)[:10]
            hauptliste['segments'].append(j_segment)

            setop_matrix.append(setop_matrix_row)
            hauptliste_matrix.append(hauptliste_matrix_row)
            if segment['index'] != 1:
                hauptliste_delta_matrix.append(hauptliste_delta_matrix_row)
            setop_matrix_row = []
            hauptliste_matrix_row = []
            hauptliste_delta_matrix_row = []

            segment['word_count']
            seg_prev = j_segment

        hauptliste['lchart_ms_percent_vals'] = line_ms_pc_values
        hauptliste['lchart_ms_delta_vals'] = line_ms_delta_values
        hauptliste['lchart_layer_counts'] = line_la_counts
        hauptliste['lchart_layer_freq_vals'] = line_la_freq_values
        hauptliste['lchart_layer_delta_vals'] = line_la_delta_values
        hauptliste['lchart_segment_labels'] = segment_labels
        hauptliste['lchart_ref_mss'] = lchart_ref_mss
        hauptliste['lchart_ref_layers'] = lchart_ref_layers

        # ref MS/layer chart colors
        hauptliste['bchart_ref_mss'] = bchart_ref_mss
        hauptliste['bchart_ref_mss_colors'] = ref_settings['bchart_ref_mss_colors']
        hauptliste['lchart_ref_mss_colors'] = ref_settings['lchart_ref_mss_colors']
        hauptliste['lchart_ref_layer_colors'] = {
            'M': '#f33',
            'D': '#fc0',
            'L': '#28a428'
        }
        hauptliste['lchart_ref_layer_colors_bw'] = {
            'M': '#eee',
            'D': '#ccc',
            'L': '#aaa'
        }

        hauptliste['vu_count'] = s.vu_count
        hauptliste['vu_no_retro_count'] = s.no_retro_count
        hauptliste['m_layer_count'] = len(s.m_readings)
        hauptliste['m_sg_layer_count'] = len(s.m_sg_readings)
        hauptliste['na_layer_count'] = len(s.na_readings)
        hauptliste['d_layer_count'] = len(s.d_readings)
        hauptliste['d_layer_readings'] = s.d_readings
        hauptliste['l_layer_count'] = len(s.l_readings)
        hauptliste['l_layer_readings'] = s.l_readings
        hauptliste['s_layer_count'] = len(s.s_readings)
        hauptliste['s_layer_readings'] = s.s_readings
        hauptliste['s_05_retro_layer_count'] = len(s.s_05_retro_readings)
        hauptliste['s_05VL5_layer_count'] = len(s.s_05VL5_readings)

        s.info('Saving Hauptlisten for', refMS)

        hlfile = s.dicerFolder + refMS + '-' + s.segmentConfig['label'] + '-hauptliste.json'
        jdata = json.dumps(hauptliste, ensure_ascii=False)
        with open(hlfile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

        # Save hauptliste CSVs
        csvfile = s.dicerFolder + refMS + '-' + s.segmentConfig['label'] + '-hauptliste.csv'
        with open(csvfile, 'w+') as file:
            for row in hauptliste_matrix:
                file.write(('\t'.join(row) + '\n').encode('UTF-8'))
            file.close()

        # Save setop CSVs
        csvfile = s.dicerFolder + refMS + '-' + s.segmentConfig['label'] + '-setop.csv'
        with open(csvfile, 'w+') as file:
            for row in setop_matrix:
                file.write(('\t'.join(row) + '\n').encode('UTF-8'))
            file.close()

        csvfile = s.dicerFolder + refMS + '-' + s.segmentConfig['label'] + '-hauptliste-delta.csv'
        with open(csvfile, 'w+') as file:
            for row in hauptliste_delta_matrix:
                file.write(('\t'.join(row) + '\n').encode('UTF-8'))
            file.close()

        # Save layer-per-segment stats
        s.outputPerSegment('M', hauptliste, 'majority_count', 'majority_count_prev', 'majority_count_delta', 'majority_count_delta_pc', None)
        s.outputPerSegment('D', hauptliste, 'D_count', 'D_count_prev', 'D_count_delta', 'D_count_delta_pc', 'D_labels')
        s.outputPerSegment('L', hauptliste, 'L_count', 'L_count_prev', 'L_count_delta', 'L_count_delta_pc', 'L_labels')
        s.outputPerSegment('S', hauptliste, 'S_count', 'S_count_prev', 'S_count_delta', 'S_count_delta_pc', 'S_labels')

        s.outputPerSegmentCorrector(hauptliste, '01A')
        s.outputPerSegmentCorrector(hauptliste, '01C1')
        s.outputPerSegmentCorrector(hauptliste, '05A')
        s.outputPerSegmentCorrector(hauptliste, '05B')

        s.outputPerSegmentGroup(hauptliste, 'F03')
        s.outputPerSegmentGroup(hauptliste, 'F1')
        s.outputPerSegmentGroup(hauptliste, 'F13')
        s.outputPerSegmentGroup(hauptliste, 'C565')
        s.outputPerSegmentGroup(hauptliste, 'CP45')

    def outputPerSegmentGroup(s, hauptliste, group_key):
        csvfile = s.dicerFolder + s.segmentConfig['label'] + '-' + group_key + '-segment-stats.csv'
        file = open(csvfile, 'w+')
        file.write('Segment\tRange\tWord Count\tMultiplier\tCount\tLast Count\tΔ Count\tPercent Δ\tCount (Calibrated)\tLast Count (Calibrated)\tΔ Count (Calibrated)\tPercent Δ (Calibrated)\tReadings\n')
        for j_segment in hauptliste['segments']:
            group = j_segment['group_data'][group_key]
            count = group['D_group_count']
            prev_count = group['D_group_count_prev']
            count_delta = group['D_group_count_delta']
            count_delta_pc = group['D_group_count_delta_pc']
            labels = group['labels']
            multiplier = j_segment['word_count_multiplier']
            last_multiplier = j_segment['last_word_count_multiplier']
            cal_count = round(multiplier * count, 1)
            cal_prev_count = round(last_multiplier * prev_count, 1)
            cal_count_delta = cal_count - cal_prev_count
            cal_count_delta_pc = round(cal_count / cal_prev_count, 3) if cal_prev_count != 0 else 0.0

            file.write(str(j_segment['index']) + '\t' + j_segment['label'] + '\t' + str(j_segment['word_count']) + '\t' + str(round(multiplier, 3)) + '\t' + str(count) + '\t' + str(prev_count) + '\t' + str(count_delta) + '\t' + str(count_delta_pc) + '\t' + str(cal_count) + '\t' + str(cal_prev_count) + '\t' + str(cal_count_delta) + '\t' + str(cal_count_delta_pc) + '\t' + labels + '\n')

        file.close()

    def outputPerSegment(s, file_key, hauptliste, count_key, prev_count_key, count_delta_key, count_delta_pc_key, verse_refs):
        csvfile = s.dicerFolder + s.segmentConfig['label'] + '-' + file_key + '-segment-stats.csv'
        file = open(csvfile, 'w+')
        file.write('Segment\tRange\tWord Count\tMultiplier\tCount\tLast Count\tΔ Count\tPercent Δ\tCount (Calibrated)\tLast Count (Calibrated)\tΔ Count (Calibrated)\tPercent Δ (Calibrated)\tReadings\n')
        for j_segment in hauptliste['segments']:
            count = j_segment[count_key]
            prev_count = j_segment[prev_count_key]
            count_delta = j_segment[count_delta_key]
            count_delta_pc = j_segment[count_delta_pc_key]
            multiplier = j_segment['word_count_multiplier']
            last_multiplier = j_segment['last_word_count_multiplier']
            cal_count = round(multiplier * count, 1)
            cal_prev_count = round(last_multiplier * prev_count, 1)
            cal_count_delta = cal_count - cal_prev_count
            cal_count_delta_pc = round(cal_count / cal_prev_count, 3) if cal_prev_count != 0 else 0.0
            ref_str = ''
            if verse_refs:
                ref_str = j_segment[verse_refs]

            file.write(str(j_segment['index']) + '\t' + j_segment['label'] + '\t' + str(j_segment['word_count']) + '\t' + str(round(multiplier, 3)) + '\t' + str(count) + '\t' + str(prev_count) + '\t' + str(count_delta) + '\t' + str(count_delta_pc) + '\t' + str(cal_count) + '\t' + str(cal_prev_count) + '\t' + str(cal_count_delta) + '\t' + str(cal_count_delta_pc) + '\t' + ref_str + '\n')

        file.close()

    def outputPerSegmentCorrector(s, hauptliste, corrector_key):
        csvfile = s.dicerFolder + s.segmentConfig['label'] + '-' + corrector_key + '-segment-stats.csv'
        file = open(csvfile, 'w+')
        file.write('Segment\tRange\tWord Count\tMultiplier\tCount\tLast Count\tΔ Count\tPercent Δ\tCount (Calibrated)\tLast Count (Calibrated)\tΔ Count (Calibrated)\tPercent Δ (Calibrated)\tReadings\n')
        for j_segment in hauptliste['segments']:
            count = j_segment['correctors'][corrector_key]['count']
            prev_count = j_segment['correctors'][corrector_key]['prev_count']
            count_delta = j_segment['correctors'][corrector_key]['count_delta']
            count_delta_pc = j_segment['correctors'][corrector_key]['count_delta_pc']
            multiplier = j_segment['word_count_multiplier']
            last_multiplier = j_segment['last_word_count_multiplier']
            cal_count = round(multiplier * count, 1)
            cal_prev_count = round(last_multiplier * prev_count, 1)
            cal_count_delta = cal_count - cal_prev_count
            cal_count_delta_pc = round(cal_count / cal_prev_count, 3) if cal_prev_count != 0 else 0.0

            file.write(str(j_segment['index']) + '\t' + j_segment['label'] + '\t' + str(j_segment['word_count']) + '\t' + str(round(multiplier, 3)) + '\t' + str(count) + '\t' + str(prev_count) + '\t' + str(count_delta) + '\t' + str(count_delta_pc) + '\t' + str(cal_count) + '\t' + str(cal_prev_count) + '\t' + str(cal_count_delta) + '\t' + str(cal_count_delta_pc) + '\t' + j_segment['correctors'][corrector_key]['labels'] + '\n')

        file.close()

    def computeUnions(s, refMS):
        c = s.config
        unionMSS = c.get('unionMSS')
        file = open(s.dicerFolder + refMS + '-' + s.segmentConfig['label'] + '-unions.csv', 'w+')
        file.write('MSS\tMSS Count\tAVG\tSTD\n')
        for i in range(1,9):
            s.info('Processing combinations of', str(i))
            combos = itertools.combinations(unionMSS, i)
            for cmb in combos:
                ratios = []
                for sidx, segment in enumerate(s.dicer_segments):
                    u_refs = set()
                    for ms in cmb:
                        if not segment['ms_refs_d'].has_key(ms):
                            continue
                        u_refs = u_refs | set(segment['ms_refs_d'][ms])
                    ref_data = segment['ref_data'][refMS]
                    D_count = len(ref_data['D_readings'])
                    ratio = round(len(u_refs) * 1.0 / D_count, 3)
                    ratios.append(ratio)
                avg = round(np.mean(ratios), 3)
                std = round(np.std(ratios), 3)
                file.write(' '.join(cmb) + '\t' + str(i) + '\t' + str(avg) + '\t' + str(std) + '\n')
        file.close()

    def runHauptliste(s, refMS):
        s.prepareHauptlisten(refMS)
        s.computeHauptlisten(refMS)
        #s.computeUnions(refMS) # expensive!

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        s.subsingular = c.get('subsingularVariants')
        s.latinLayerCore = c.get('latinLayerCoreVariants')
        s.latinLayerMulti = c.get('latinLayerMultiVariants')

        if o.range:
            s.range_id = o.range
        else:
            s.range_id = c.get('defaultRange')

        if o.refMSS:
            s.refMS_IDs = o.refMSS.split(',')
        else:
            s.refMS_IDs = c.get('referenceMSS')

        if o.segmentConfig:
            s.segmentConfig = c.get('segmentConfiguration')[o.segmentConfig]
            s.segmentConfig['label'] = o.segmentConfig

        if o.hauptliste:
            s.doHauptliste = True

        if o.qca:
            s.doQCA = True

        if o.offsets:
            s.doOffsets = True

        s.dicerFolder = c.get('dicerFolder')
        if not os.path.exists(s.dicerFolder):
            os.makedirs(s.dicerFolder)

        s.qcaSet = c.get('dicerQCASet')

        s.statsFolder = c.get('dicerStatsFolder')
        if not os.path.exists(s.statsFolder):
            os.makedirs(s.statsFolder)

        is_refresh = False
        if o.refreshCache:
            is_refresh = True

        # load variant data
        s.rangeMgr = RangeManager()
        s.rangeMgr.load(is_refresh)

        s.variantModel = s.rangeMgr.getModel(s.range_id)

        for rms in s.refMS_IDs:
            s.dicer_segments = []
            s.diceText(rms)

            if s.doQCA:
                s.runQCA(rms)

            if s.doHauptliste:
                s.runHauptliste(rms)

            # Segment list
            csvfile = s.dicerFolder + rms + '-' + s.segmentConfig['label'] + '-segment-list.csv'
            with open(csvfile, 'w+') as file:
                file.write('Segment Label\t' + rms + ' words\n')
                for segment in s.dicer_segments:
                    file.write(segment['label'] + '\t' + str(segment['word_count']) + '\n')
                file.close()

        s.info('Done')

# Invoke via entry point
#
# Output only segment divisions
# dicer.py -v -a c01-16 -R 05
#
# Generate segments with QCA analysis
# dicer.py -v -a c01-16 -R 05 -Q
#
# Generate regular block-sized segments (default configuration)
# dicer.py -v -a c01-16 -R 05 -H
#
# Generate segments with named configuration (e.g. micro configuration)
# dicer.py -v -a c01-16 -R 05 -G micro -H
Dicer().main(sys.argv[1:])
