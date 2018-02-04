#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, re
from collections import OrderedDict
from object.util import *
from utility.config import *
from utility.options import *

def sortAgrees(a1, a2):
    if a1['percent'] < a2['percent']:
        return 1
    if a1['percent'] > a2['percent']:
        return -1
    return 0

class CorAnalyzer:

    def __init__(s):
        s.config = None
        s.options = None

        s.refMS = ''
        s.vus = []
        s.hands = {}
        s.hand_combos = {}

        s.greekMSS = []
        s.latinMSS = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def isBezae(s):
        return True if s.refMS == '05' else False # 01

    def isSinai(s):
        return True if s.refMS == '01' else False # 05

    def isHand(s, part):
        if not part:
            return False

        if s.isSinai():
            return True if part in Util.SINAI_HANDS else False
        else: # Bezae
            return True if part in Util.BEZAE_HANDS else False

    def initHands(s):
        if s.isSinai():
            for hand in Util.SINAI_HANDS:
                s.hands[hand] = s.initHand(hand)
        else: # Bezae
            for hand in Util.BEZAE_HANDS:
                s.hands[hand] = s.initHand(hand)

    def initHand(s, name):
        hand = {}
        hand['name'] = name
        hand['vus'] = []
        hand['total_agrees'] = {}
        hand['mainstream_agrees'] = {}
        hand['nonmainstream_agrees'] = {}
        hand['nonms_extant'] = {}
        for ms in s.greekMSS:
            hand['total_agrees'][ms] = 0
            hand['mainstream_agrees'][ms] = 0
            hand['nonmainstream_agrees'][ms] = 0
            hand['nonms_extant'][ms] = 0
        for ms in s.latinMSS:
            hand['total_agrees'][ms] = 0
            hand['mainstream_agrees'][ms] = 0
            hand['nonmainstream_agrees'][ms] = 0
            hand['nonms_extant'][ms] = 0
        hand['mainstream_readings'] = []
        hand['nonmainstream_readings'] = []
        hand['sorted_nonms_agrees'] = []
        hand['singular_readings'] = []
        return hand

    def initVU(s):
        vu = {}
        vu['hands'] = []
        vu['readings'] = []
        return vu

    def addAgreement(s, hand, ms):
        if len(hand['nonmainstream_readings']) == 0 or hand['nonms_extant'][ms] * 1.0 / len(hand['nonmainstream_readings']) < 0.5:
            return

        ms_agree = {}
        ms_agree['ms'] = ms
        ms_agree['agreements'] = hand['nonmainstream_agrees'][ms]
        ms_agree['extant'] = hand['nonms_extant'][ms]
        ms_agree['percent'] = round(1.0 * ms_agree['agreements'] / ms_agree['extant'] if ms_agree['extant'] != 0 else 0, 3)
        hand['sorted_nonms_agrees'].append(ms_agree)

    def majorityStats(s, file, h_info, c_total):
        h_total = len(h_info['vus'])
        m_total = len(h_info['mainstream_readings'])

        file.write(h_info['name'] + '\t')
        file.write(str(m_total) + '\t')
        file.write(str(h_total) + '\t')

        m_pc = round(1.0 * m_total / h_total if h_total != 0 else 0, 3)
        file.write(str(m_pc * 100) + '% \n')

    def nonmajorityStats(s, file, h_info, c_total):
        file.write('Corrector ' + h_info['name'] + '\n')
        file.write('MS\tAgreements\tTotal Extant\tPercentage\n')
        for agree in h_info['sorted_nonms_agrees']:
            if agree['percent'] < 0.2:
                break
            file.write(agree['ms'] + '\t' + str(agree['agreements']) + '\t' + str(agree['extant']) + '\t' + str(agree['percent'] * 100) + '%\n')
        file.write('\n')

    def singularStats(s, file, h_info, c_total):
        h_total = len(h_info['vus'])
        s_total = len(h_info['singular_readings'])

        file.write(h_info['name'] + '\t')
        file.write(str(s_total) + '\t')
        file.write(str(h_total) + '\t')

        s_pc = round(1.0 * s_total / h_total if h_total != 0 else 0, 3)
        file.write(str(s_pc * 100) + '% \n')

    def summarizeHand(s, file, h_info, c_total):
        h_total = len(h_info['vus'])

        file.write(h_info['name'] + '\t')
        file.write(str(h_total) + '\t')

        h_pc = round(1.0 * h_total / c_total if c_total != 0 else 0, 3)
        file.write(str(h_pc * 100) + '% (' + str(h_total) + '/' + str(c_total) + ')' + '\n')

    def summarizeCombo(s, file, ms_hands, cmb_set, cmb_total, cor_total):
        c_str = ''
        for hand in ms_hands:
            if hand in cmb_set:
                if c_str:
                    c_str = c_str + ', '
                c_str = c_str + hand
        c_pc = round(1.0 * cmb_total / cor_total if cor_total != 0 else 0, 3)

        file.write(c_str + '\t')
        file.write(str(cmb_total) + '\t')
        file.write(str(c_pc * 100) + '% (' + str(cmb_total) + '/' + str(cor_total) + ')' + '\n')

    def summarizeHands(s, file, c_total):
        c = s.config

        file.write('Corrector\tCorrections\tPercent of Total\n')
        if s.isSinai():
            for hand in Util.SINAI_HANDS:
                if hand == '01*': continue
                s.summarizeHand(file, s.hands[hand], c_total)
        else: # Bezae
            for hand in Util.BEZAE_HANDS:
                if hand == '05*': continue
                s.summarizeHand(file, s.hands[hand], c_total)
        file.write('Total\t' + str(c_total) + '\t100% (' + str(c_total) + '/' + str(c_total) + ')\n\n')

        file.write('Combination\tCorrections\tPercent of Total\n')
        for cmb_set, cmb_total in s.hand_combos.iteritems():
            if s.isSinai():
                s.summarizeCombo(file, Util.SINAI_HANDS, cmb_set, cmb_total, c_total)
            else: # Bezae
                s.summarizeCombo(file, Util.BEZAE_HANDS, cmb_set, cmb_total, c_total)
                
        file.write('\n')

        file.write('Corrector\tMajority Readings\tCorrector Readings\tPercentage\n')
        if s.isSinai():
            for hand in Util.SINAI_HANDS:
                s.majorityStats(file, s.hands[hand], c_total)
        else: # Bezae
            for hand in Util.BEZAE_HANDS:
                s.majorityStats(file, s.hands[hand], c_total)
        file.write('\n')

        file.write('Corrector\tSingular Readings\tCorrector Readings\tPercentage\n')
        if s.isSinai():
            for hand in Util.SINAI_HANDS:
                s.singularStats(file, s.hands[hand], c_total)
        else: # Bezae
            for hand in Util.BEZAE_HANDS:
                s.singularStats(file, s.hands[hand], c_total)
        file.write('\n')

        if s.isSinai():
            for hand in Util.SINAI_HANDS:
                s.nonmajorityStats(file, s.hands[hand], c_total)
        else: # Bezae
            for hand in Util.BEZAE_HANDS:
                s.nonmajorityStats(file, s.hands[hand], c_total)
        file.write('\n')

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        MODE_LABEL = 'LABEL'
        MODE_IGNORE = 'IGNORE'
        MODE_TABLE = 'TABLE'

        infile_name = ''
        infile = None
        cachefile = None
        if o.file:
            infile_name = o.file
            infile = c.get('inputFolder') + infile_name + '.csv'
        else:
            s.info('Please specify input file with -f [filename]')
            return

        s.refMS = o.refMSS
        if not s.refMS:
            s.info('Please specify reference MS with -R [GA]')
            return

        if s.refMS not in Util.CORRECTOR_MSS:
            s.info('01 and 05 are currently the only supported reference MSS')
            return

        re_label = re.compile('^((\d{1,2})\.(\d{1,2})\.([0-9\-,]{1,}))(,(\d{1,2})\.([0-9\-,]{1,})){0,1}(,(\d{1,2})\.([0-9\-,]{1,})){0,1}$')
        re_reading = re.compile('^((\d{1,2})\.(\d{1,2})\.([0-9\-,]{1,}))(,(\d{1,2})\.([0-9\-,]{1,})){0,1}(,(\d{1,2})\.([0-9\-,]{1,})){0,1}([a-z])$')

        s.greekMSS = c.get('greekMSS')
        s.latinMSS = c.get('latinMSS')
        s.initHands()

        csvdata = ''
        with open(infile, 'r') as file:
            s.info('reading', infile)
            csvdata = file.read().decode('utf-8')
            file.close()

        mode = MODE_LABEL
        cur_vu = {}
        ms_headers = []
        cur_hands = []

        rows = csvdata.split('\n')
        for rdx, row in enumerate(rows):
            parts = row.split('\t')
            if not parts or len(parts) == 1 or (not parts[0] and not parts[1]): # empty line
                continue

            rs_label = re_label.search(parts[0])
            if rs_label: # label
                if cur_vu and cur_vu['readings']:
                    s.vus.append(cur_vu)

                if cur_hands:
                    h_key = frozenset(cur_hands)
                    if not s.hand_combos.has_key(h_key):
                        s.hand_combos[h_key] = 0
                    s.hand_combos[h_key] = s.hand_combos[h_key] + 1

                cur_vu = s.initVU()
                cur_hands = []
                cur_vu['label'] = parts[0]
                mode = MODE_LABEL
                continue

            if mode == MODE_IGNORE:
                continue

            if parts[0] == 'x': # ignore flag
                mode = MODE_IGNORE
                cur_vu = s.initVU()
                cur_hands = []
                continue

            if s.isBezae() and parts[1] == 'pm': # skip 05 primary hand
                mode = MODE_IGNORE
                cur_vu = s.initVU()
                cur_hands = []
                continue

            if mode == MODE_LABEL and s.isHand(parts[1]): # hand data
                hand = {}
                hand['name'] = parts[1]
                hand['value'] = parts[2]
                cur_vu['hands'].append(hand)
                if hand['value'] != '---':
                    s.hands[hand['name']]['vus'].append(cur_vu['label'])
                if parts[1] != '01*' and parts[1] != '05*':
                    cur_hands.append(parts[1])
                continue

            if parts[0] == 'sort_id':
                ms_headers = parts
                mode = MODE_TABLE
                continue

            if MODE_TABLE and re_reading.search(parts[0]): # reading data
                reading = {}
                reading['mss'] = {}
                reading['sort_id'] = parts[0]
                reading['reading_id'] = parts[1]
                reading['reading_text'] = parts[2]
                reading['correctors'] = []
                if s.isSinai():
                    if parts[3]: reading['correctors'].append('A')
                    if parts[4]: reading['correctors'].append('C1')
                    if parts[5]: reading['correctors'].append('C2')
                else: # Bezae
                    if parts[3]: reading['correctors'].append('sm')
                    if parts[4]: reading['correctors'].append('A')
                    if parts[5]: reading['correctors'].append('B')
                    if parts[6]: reading['correctors'].append('C')
                    if parts[7]: reading['correctors'].append('D')
                    if parts[8]: reading['correctors'].append('E')
                    if parts[9]: reading['correctors'].append('H')
                start = 6 if s.isSinai() else 10 # Bezae
                orig = '0'
                is_majority = False
                is_singular_corrector = True
                for i in range(start, len(ms_headers)):
                    if parts[i] == '-':
                        ms_key = ms_headers[i]
                        if s.isSinai() and ms_key == '01':
                            orig = '-'
                        elif s.isBezae() and ms_key == '05':
                            orig = '-'
                    elif parts[i] == '1':
                        ms_key = ms_headers[i]
                        if ms_key == '35':
                            is_majority = True
                        if s.isSinai() and ms_key == '01':
                            orig = '1'
                        elif s.isBezae() and ms_key == '05':
                            orig = '1'
                        reading['mss'][ms_key] = 1
                        is_singular_corrector = False

                cor_list = Util.SINAI_HANDS if s.isSinai() else Util.BEZAE_HANDS
                for i in range(start, len(ms_headers)):
                    ms_key = ms_headers[i]
                    for hand in cor_list:
                        if not hand in reading['correctors'] and hand != '01*' and hand != '05*':
                            continue

                        if parts[i] == '1':
                            s.hands[hand]['total_agrees'][ms_key] = s.hands[hand]['total_agrees'][ms_key] + 1
                            if is_majority:
                                s.hands[hand]['mainstream_agrees'][ms_key] = s.hands[hand]['mainstream_agrees'][ms_key] + 1
                            else:
                                s.hands[hand]['nonmainstream_agrees'][ms_key] = s.hands[hand]['nonmainstream_agrees'][ms_key] + 1

                        if not is_majority and (parts[i] == '0' or parts[i] == '1'):
                            if hand == '01*' or hand == '05*':
                                if orig == '1':
                                    s.hands[hand]['nonms_extant'][ms_key] = s.hands[hand]['nonms_extant'][ms_key] + 1
                            else:
                                s.hands[hand]['nonms_extant'][ms_key] = s.hands[hand]['nonms_extant'][ms_key] + 1

                for hand in cor_list:
                    if not hand in reading['correctors'] and hand != '01*' and hand != '05*':
                        continue

                    if is_majority:
                        if s.isSinai() and hand == '01*':
                            if orig == '1':
                                s.hands[hand]['mainstream_readings'].append(reading['reading_id'])
                        elif s.isBezae() and hand == '05*':
                            if orig == '1':
                                s.hands[hand]['mainstream_readings'].append(reading['reading_id'])
                        else:
                            s.hands[hand]['mainstream_readings'].append(reading['reading_id'])
                    elif is_singular_corrector:
                        s.hands[hand]['singular_readings'].append(reading['reading_id'])
                    else:
                        if s.isSinai() and hand == '01*':
                            if orig == '1':
                                s.hands[hand]['nonmainstream_readings'].append(reading['reading_id'])
                        elif s.isBezae() and hand == '05*':
                            if orig == '1':
                                s.hands[hand]['nonmainstream_readings'].append(reading['reading_id'])
                        else:
                            s.hands[hand]['nonmainstream_readings'].append(reading['reading_id'])

                cur_vu['readings'].append(reading)
                continue

        c_total = 0
        if s.isSinai():
            for hand in Util.SINAI_HANDS:
                h_map = s.hands[hand]
                for ms in s.greekMSS:
                    if ms != '01':
                        s.addAgreement(h_map, ms)
                if hand == '01*':
                    continue
                c_total = c_total + len(h_map['vus'])
        else: # Bezae
            for hand in Util.BEZAE_HANDS:
                h_map = s.hands[hand]
                for ms in s.greekMSS:
                    if ms != '05':
                        s.addAgreement(h_map, ms)
                if hand == '05*':
                    continue
                c_total = c_total + len(h_map['vus'])

        for h_key, h_map in s.hands.iteritems():
            h_map['sorted_nonms_agrees'] = sorted(h_map['sorted_nonms_agrees'], cmp=sortAgrees)

        r_file = c.get('outputFolder') + infile_name + '-hand-analysis.csv'
        file = open(r_file, 'w+')

        s.summarizeHands(file, c_total)

        file.close()

        result_file = c.get('outputFolder') + infile_name + '-data.json'
        jdata = json.dumps(s.vus, ensure_ascii=False)
        with open(result_file, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

# Produce correction analysis for reference MSS
# corAnalyzer.py -v -R 05 -f bezaecor-01
# corAnalyzer.py -v -R 01 -f sinaicor-01
CorAnalyzer().main(sys.argv[1:])
