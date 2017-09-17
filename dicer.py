#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, json, re, subprocess

from object.jsonEncoder import *
from object.rangeManager import *
from object.truthTable import *
from object.util import *

from utility.config import *
from utility.options import *

def sortHauptliste(mi1, mi2):
    pc1 = mi1['D_ratio']
    pc2 = mi2['D_ratio']

    if pc1 < pc2:
        return 1
    elif pc1 > pc2:
        return -1

    return 0

class Dicer:

    def __init__(s):
        s.dicerFolder = 'dicer-results'
        s.statsFolder = 'static/stats/dicer/'
        s.range_id = ''
        s.rangeMgr = None
        s.qcaSet = 'basic'
        s.variantModel = None

        s.dicer_segments = []
        s.segment_min = 300
        s.segment_size = 375
        s.segment_offset = 187

        s.doHauptliste = False
        s.doQCA = False

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def diceText(s, ms):
        s.info('Dicing text')

        c_count = 0
        v_count = 0
        w_count = 0

        cur_c = 0
        cur_v = 0
        match_forms = ['om.', '-', '~', ' ', '']

        segment = {}
        segment_counter = 0

        offset = {}
        offset_counter = s.segment_offset

        segment_index = 1

        logfile = s.dicerFolder + ms + '-words.log'
        with open(logfile, 'w+') as file:
            for addr in s.variantModel['addresses']:
                if int(addr.chapter_num) != cur_c:
                    cur_c = int(addr.chapter_num)
                    c_count = c_count + 1

                if addr.verse_num != cur_v:
                    if segment_counter > s.segment_size:
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

                    if offset_counter > s.segment_size:
                        offset['end_chapter'] = str(cur_c)
                        offset['end_verse'] = str(cur_v)
                        offset['index'] = segment_index
                        offset['label'] = offset['start_chapter'] + ',' + offset['start_verse'] + '-' + offset['end_chapter'] + ',' + offset['end_verse']
                        offset['address_count'] = len(offset['addresses'])
                        offset['word_count'] = offset_counter

                        if len(s.dicer_segments) > 0:
                            s.dicer_segments.append(offset)
                            segment_index = segment_index + 1

                        offset_counter = 0
                        offset = {}

                    cur_v = addr.verse_num
                    v_count = v_count + 1

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

            file.close()

            if (segment_counter > s.segment_min):
                segment['end_chapter'] = str(cur_c)
                segment['end_verse'] = str(cur_v)
                segment['index'] = segment_index
                segment['label'] = segment['start_chapter'] + ',' + segment['start_verse'] + '-' + segment['end_chapter'] + ',' + segment['end_verse']
                segment['address_count'] = len(segment['addresses'])
                segment['word_count'] = segment_counter
                s.dicer_segments.append(segment)

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

    def isLatinLayer(s, greek_counter, latin_counter):
        is_latin = False
        if latin_counter >= greek_counter and latin_counter > 2 and greek_counter <= 3:
            is_latin = True
        else:
            if latin_counter >= greek_counter and latin_counter > 1 and greek_counter <= 2:
                is_latin = True
            elif latin_counter >= greek_counter and latin_counter > 0 and greek_counter <= 1:
                is_latin = True
        return is_latin

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

    def prepareHauptlisten(s, refMS):
        for segment in s.dicer_segments:
            s.info('Generating Hauptliste for', segment['label'])

            if not segment.has_key('ref_data'):
                segment['ref_data'] = {}

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

            for addr in segment['addresses']:
                for vu in addr.variation_units:
                    if not vu.startingAddress:
                        vu.startingAddress = addr

                    if vu.isSingular() or vu.isReferenceSingular(refMS):
                        continue

                    m_reading = vu.getReadingForManuscript('35')
                    r_reading = vu.getReadingForManuscript(refMS)

                    if not r_reading:
                        continue

                    if r_reading == m_reading:
                        ref_data['majority_count'] = ref_data['majority_count'] + 1
                        continue


                    reading_info = {}
                    reading_info['mss'] = []
                    reading_info['variant_label'] = vu.label
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
                    if (s.isLatinLayer(len(greek_mss), len(latin_mss))):
                        reading_info['L_layer'] = True
                        reading_info['D_layer'] = False
                    else:
                        reading_info['L_layer'] = False
                        reading_info['D_layer'] = True

                    if reading_info['L_layer']:
                        ref_data['L_readings'].append(reading_info)
                    elif reading_info['D_layer']:
                        ref_data['D_readings'].append(reading_info)
                    ref_data['nonM_readings'].append(reading_info)

                    # Family profile scores
                    reading_info['c565_scores'] = s.isCluster565(greek_mss)
                    reading_info['f03_scores'] = s.isFamily03(greek_mss)
                    reading_info['f1_scores'] = s.isFamily1(greek_mss)
                    reading_info['f13_scores'] = s.isFamily13(greek_mss)

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

    def computeHauptlisten(s, refMS):
        hauptliste = {}
        hauptliste['segments'] = []
        hauptliste['ref_ms'] = refMS
        for segment in s.dicer_segments:
            ref_data = segment['ref_data'][refMS]

            j_segment = {}
            j_segment['majority_count'] = ref_data['majority_count']
            j_segment['nonM_count'] = len(ref_data['nonM_readings'])
            j_segment['D_count'] = len(ref_data['D_readings'])
            j_segment['L_count'] = len(ref_data['L_readings'])
            j_segment['index'] = segment['index']
            j_segment['address_count'] = segment['address_count']
            j_segment['word_count'] = segment['word_count']
            j_segment['label'] = segment['label']
            j_segment['greek_mss'] = []
            j_segment['latin_mss'] = []
            j_segment['D_readings'] = []
            j_segment['L_readings'] = []

            j_profiles = {}
            j_profiles['f03_readings'] = []
            j_profiles['f1_readings'] = []
            j_profiles['f13_readings'] = []
            j_profiles['c565_readings'] = []
            j_profiles['032_readings'] = []

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

            for ms in s.variantModel['manuscripts']:
                if ms == refMS:
                    continue

                msdat = {}
                msdat['manuscript'] = ms

                msdat['D_instance_count'] = 0
                if ref_data['D_instances'].has_key(ms):
                    msdat['D_instance_count'] = len(ref_data['D_instances'][ms])

                if msdat['D_instance_count'] <= 1:
                    continue

                msdat['D_lac_count'] = 0
                if ref_data['D_lac'].has_key(ms):
                    msdat['D_lac_count'] = len(ref_data['D_lac'][ms])

                msdat['D_count'] = j_segment['D_count'] - msdat['D_lac_count']

                a_ratio = 0.0
                if msdat['D_count']:
                    a_ratio = msdat['D_instance_count'] * 1.0 / msdat['D_count']
                    a_ratio = '%.3f' % round(a_ratio, 3)
                msdat['D_ratio'] = a_ratio

                if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
                    j_segment['latin_mss'].append(msdat)
                else:
                    j_segment['greek_mss'].append(msdat)

            j_segment['greek_mss'] = sorted(j_segment['greek_mss'], cmp=sortHauptliste)
            j_segment['latin_mss'] = sorted(j_segment['latin_mss'], cmp=sortHauptliste)
            hauptliste['segments'].append(j_segment)

        s.info('Saving Hauptlisten for', refMS)

        hlfile = s.dicerFolder + refMS + '-hauptliste.json'
        jdata = json.dumps(hauptliste, ensure_ascii=False)
        with open(hlfile, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

    def runHauptliste(s, refMS):
        s.prepareHauptlisten(refMS)
        s.computeHauptlisten(refMS)

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        if o.range:
            s.range_id = o.range
        else:
            s.range_id = c.get('defaultRange')

        if o.refMSS:
            s.refMS_IDs = o.refMSS.split(',')
        else:
            s.refMS_IDs = c.get('referenceMSS')

        if o.hauptliste:
            s.doHauptliste = True

        if o.qca:
            s.doQCA = True

        s.dicerFolder = c.get('dicerFolder')
        if not os.path.exists(s.dicerFolder):
            os.makedirs(s.dicerFolder)

        s.segment_size = c.get('segmentSize')
        s.segment_min = c.get('segmentMin')
        s.segment_offset = c.get('segmentOffset')

        s.qcaSet = c.get('dicerQCASet')

        s.statsFolder = c.get('dicerStatsFolder')
        if not os.path.exists(s.statsFolder):
            os.makedirs(s.statsFolder)

        # load variant data
        s.rangeMgr = RangeManager()
        s.rangeMgr.load()

        s.variantModel = s.rangeMgr.getModel(s.range_id)

        for rms in s.refMS_IDs:
            s.dicer_segments = []
            s.diceText(rms)

            if s.doQCA:
                s.runQCA(rms)

            if s.doHauptliste:
                s.runHauptliste(rms)

        s.info('Done')

# Invoke via entry point
# dicer.py -v -a c01-16 -R 05
Dicer().main(sys.argv[1:])
