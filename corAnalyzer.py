#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, re
from collections import OrderedDict
from object.util import *
from utility.config import *
from utility.options import *

class CorAnalyzer:

    CORRECTOR_MSS = ['01', '05']

    BEZAE_HANDS = ['05*','sm','A','B','C','D','E','H','A/B']
    SINAI_HANDS = ['01*','A','C1','C2']

    def __init__(s):
        s.config = None
        s.options = None

        s.refMS = ''
        s.vus = []

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
            return True if part in CorAnalyzer.SINAI_HANDS else False
        else: # Bezae
            return True if part in CorAnalyzer.BEZAE_HANDS else False

    def initVU(s):
        vu = {}
        vu['hands'] = []
        vu['readings'] = []
        return vu

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        MODE_LABEL = 'LABEL'
        MODE_IGNORE = 'IGNORE'
        MODE_TABLE = 'TABLE'

        re_label = re.compile('^((\d{1,2})\.(\d{1,2})\.([0-9\-,]{1,}))(,(\d{1,2})\.([0-9\-,]{1,})){0,1}(,(\d{1,2})\.([0-9\-,]{1,})){0,1}$')
        re_reading = re.compile('^((\d{1,2})\.(\d{1,2})\.([0-9\-,]{1,}))(,(\d{1,2})\.([0-9\-,]{1,})){0,1}(,(\d{1,2})\.([0-9\-,]{1,})){0,1}([a-z])$')

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

        if s.refMS not in CorAnalyzer.CORRECTOR_MSS:
            s.info('01 and 05 are currently the only supported reference MSS')
            return

        csvdata = ''
        with open(infile, 'r') as file:
            s.info('reading', infile)
            csvdata = file.read().decode('utf-8')
            file.close()

        mode = MODE_LABEL
        cur_vu = {}
        ms_headers = []

        rows = csvdata.split('\n')
        for rdx, row in enumerate(rows):
            parts = row.split('\t')
            if not parts or len(parts) == 1 or (not parts[0] and not parts[1]): # empty line
                continue

            rs_label = re_label.search(parts[0])
            if rs_label: # label
                if cur_vu and cur_vu['readings']:
                    s.vus.append(cur_vu)

                cur_vu = s.initVU()
                cur_vu['label'] = parts[0]
                mode = MODE_LABEL
                continue

            if mode == MODE_IGNORE:
                continue

            if parts[0] == 'x': # ignore flag
                mode = MODE_IGNORE
                cur_vu = s.initVU()
                continue

            if s.isBezae() and parts[1] == 'pm': # skip 05 primary hand
                mode = MODE_IGNORE
                cur_vu = s.initVU()
                continue

            if mode == MODE_LABEL and s.isHand(parts[1]): # hand data
                hand = {}
                hand['name'] = parts[1]
                hand['value'] = parts[2]
                cur_vu['hands'].append(hand)
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
                for i in range(start, len(ms_headers)):
                    if parts[i] == '1':
                        reading['mss'][ms_headers[i]] = 1
                    
                cur_vu['readings'].append(reading)
                continue

        result_file = c.get('outputFolder') + infile_name + '-data.json'
        jdata = json.dumps(s.vus, ensure_ascii=False)
        with open(result_file, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

# Produce harmonization analysis for reference MSS
# corAnalyzer.py -v -R 05 -f bezaecor-01
# corAnalyzer.py -v -R 01 -f sinaicor-01
CorAnalyzer().main(sys.argv[1:])
