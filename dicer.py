#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, json, re, subprocess

from object.jsonEncoder import *
from object.rangeManager import *
from object.truthTable import *

from utility.config import *
from utility.options import *

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
            s.runQCA(rms)

        s.info('Done')

# Invoke via entry point
# dicer.py -v -a c01-16 -R 05
Dicer().main(sys.argv[1:])
