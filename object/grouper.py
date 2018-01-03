#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, string, itertools, copy, json

from object.util import *

from utility.config import *

class Grouper:

    CUTOFF = 0.5
    ALT_CUTOFF_1 = 0.40
    ALT_CUTOFF_2 = 0.33

    MIN_READINGS = 20
    MIN_READINGS_GR = 25
    TOTAL_MAJORITY_RATIO = 0.78

    def __init__(s, r_set):
        s.config = None
        s.variantModel = None
        s.mss = []
        s.latin_mss = []

        s.maj = {}
        s.ext = {}

        s.tot_agr = {}
        s.dst_agr = {}
        s.tot_ext = {}
        s.dst_ext = {}

        s.ms_results = []

        s.latinLayerCore = None
        s.latinLayerMulti = None

        s.r_set = r_set
        s.is_greek = False
        if r_set == 'greek':
            s.is_greek = True

    def initVMap(s, map):
        for ms in s.mss:
            map[ms] = 0

    def initXMap(s, map):
        i_map = {}
        for ms in s.mss:
            i_map[ms] = 0
        for ms in s.mss:
            map[ms] = copy.deepcopy(i_map)

    def writeString(s, p_info, s_info):
        o_str = ''
        o_str = o_str + p_info['p_ms'] + '\t'
        o_str = o_str + s_info['s_ms'] + '\t'
        o_str = o_str + str(s_info['d_ratio']) + '\t'
        o_str = o_str + str(s_info['d_agree']) + '\t'
        o_str = o_str + str(s_info['d_extant']) + '\t'
        o_str = o_str + str(s_info['d_ratio'] * 100) + '% (' + str(s_info['d_agree']) + '/' + str(s_info['d_extant']) + ')' + '\t'
        o_str = o_str + str(s_info['t_ratio']) + '\t'
        o_str = o_str + str(s_info['t_agree']) + '\t'
        o_str = o_str + str(s_info['t_extant']) + '\t'
        o_str = o_str + str(s_info['t_ratio'] * 100) + '% (' + str(s_info['t_agree']) + '/' + str(s_info['t_extant']) + ')' + '\t'
        o_str = o_str + str(p_info['m_ratio']) + '\t'
        o_str = o_str + str(p_info['m_agree']) + '\t'
        o_str = o_str + str(p_info['extant']) + '\t'
        o_str = o_str + str(p_info['m_ratio'] * 100) + '% (' + str(p_info['m_agree']) + '/' + str(p_info['extant']) + ')' + '\n'
        return o_str

    def writeHeader(s):
        return 'Primary MS\tSecondary MS\tDs Ratio\tDs Agree\tDs Extant\tDs Display\tTtl Ratio\tTtl Agree\tTtl Extant\tTtl Display\tM Ratio\tM Agree\tExtant Readings\tM Display\n'

    def writeOutput(s):
        s.info('Writing GDF')
        c = s.config

        a_file = open(c.get('finderFolder') + '/grouping-all-' + s.r_set + '.csv', 'w+')
        a_file.write(s.writeHeader())

        r_file = open(c.get('finderFolder') + '/grouping-related-' + s.r_set + '.csv', 'w+')
        r_file.write(s.writeHeader())

        u_file = open(c.get('finderFolder') + '/grouping-unrelated-' + s.r_set + '.csv', 'w+')
        u_file.write(s.writeHeader())

        nodes = set()
        edge_str = ''
        for p_info in s.ms_results:
            has_nodes_0 = False
            alt1_nodes = set()
            alt1_edge_str = ''
            alt1_csv = ''
            has_nodes_1 = False
            alt2_nodes = set()
            alt2_edge_str = ''
            alt2_csv = ''
            for s_info in p_info['s_mss']:
                a_file.write(s.writeString(p_info, s_info))

                min_readings = Grouper.MIN_READINGS_GR if s.is_greek else Grouper.MIN_READINGS
                basic_test = s_info['d_extant'] >= Grouper.MIN_READINGS and s_info['t_ratio'] > p_info['m_ratio'] * Grouper.TOTAL_MAJORITY_RATIO
                p_tup = (p_info['p_ms'], p_info['m_ratio'])
                s_tup = (s_info['s_ms'], s_info['m_ratio'])

                if basic_test and s_info['d_ratio'] >= Grouper.CUTOFF:
                    r_file.write(s.writeString(p_info, s_info))

                    nodes.update([p_tup, s_tup])
                    edge_str = edge_str + p_info['p_ms'] + ',' + s_info['s_ms'] + ',' + str(s_info['d_ratio']) + '\n'
                    has_nodes_0 = True
                elif basic_test and s_info['d_ratio'] >= Grouper.ALT_CUTOFF_1:
                    alt1_nodes.update([p_tup, s_tup])
                    alt1_edge_str = alt1_edge_str + p_info['p_ms'] + ',' + s_info['s_ms'] + ',' + str(s_info['d_ratio']) + '\n'
                    alt1_csv = alt1_csv + s.writeString(p_info, s_info)
                    has_nodes_1 = True
                else:
                    if basic_test and s_info['d_ratio'] >= Grouper.ALT_CUTOFF_2:
                        alt2_nodes.update([p_tup, s_tup])
                        alt2_edge_str = alt2_edge_str + p_info['p_ms'] + ',' + s_info['s_ms'] + ',' + str(s_info['d_ratio']) + '\n'
                        alt2_csv = alt2_csv + s.writeString(p_info, s_info)
                    else:
                        u_file.write(s.writeString(p_info, s_info))

            if not has_nodes_0 and not has_nodes_1:
                nodes = nodes | alt2_nodes
                edge_str = edge_str + alt2_edge_str
                r_file.write(alt2_csv)
            elif not has_nodes_0:
                nodes = nodes | alt1_nodes
                edge_str = edge_str + alt1_edge_str
                r_file.write(alt1_csv)
                u_file.write(alt2_csv)
            else:
                u_file.write(alt1_csv)
                u_file.write(alt2_csv)

        gFile = c.get('finderFolder') + '/grouping-' + s.r_set + '.gdf'
        with open(gFile, 'w+') as g_file:
            g_file.write('nodedef>name VARCHAR,mt DOUBLE\n')
            for node in nodes:
                g_file.write(node[0] + ',' + str(node[1]) + '\n')
            g_file.write('edgedef>node1 VARCHAR,node2 VARCHAR,weight DOUBLE\n')
            g_file.write(edge_str)
            g_file.close()

        a_file.close()
        r_file.close()
        u_file.close()

    def computeRatios(s):
        s.info('Computing ratios')
        c = s.config

        for p_ms in s.mss:
            p_info = {}
            s_mss = []
            for s_ms in s.mss:
                if s_ms == p_ms:
                    continue

                dst_pc = 1.0 * s.dst_agr[p_ms][s_ms] / s.dst_ext[p_ms][s_ms] if s.dst_ext[p_ms][s_ms] != 0 else 0
                tot_pc = 1.0 * s.tot_agr[p_ms][s_ms] / s.tot_ext[p_ms][s_ms] if s.tot_ext[p_ms][s_ms] != 0 else 0

                s_info = {}
                s_info['s_ms'] = s_ms
                s_info['d_agree'] = s.dst_agr[p_ms][s_ms]
                s_info['d_extant'] = s.dst_ext[p_ms][s_ms]
                s_info['d_ratio'] = round(dst_pc, 3)
                s_info['t_agree'] = s.tot_agr[p_ms][s_ms]
                s_info['t_extant'] = s.tot_ext[p_ms][s_ms]
                s_info['t_ratio'] = round(tot_pc, 3)
                s_info['m_ratio'] = round(1.0 * s.maj[s_ms] / s.ext[s_ms] if s.ext[s_ms] != 0 else 0, 3)
                s_mss.append(s_info)

            p_info['p_ms'] = p_ms
            p_info['m_agree'] = s.maj[p_ms]
            p_info['extant'] = s.ext[p_ms]
            p_info['m_ratio'] = round(1.0 * s.maj[p_ms] / s.ext[p_ms] if s.ext[p_ms] != 0 else 0, 3)
            p_info['s_mss'] = s_mss

            s.ms_results.append(p_info)

        jsonFile = c.get('finderFolder') + '/grouping-output-' + s.r_set + '.json'
        jdata = json.dumps(s.ms_results)
        with open(jsonFile, 'w+') as j_file:
            j_file.write(jdata.encode('UTF-8'))
            j_file.close()

    def processReadings(s):
        s.info('Processing readings')
        c = s.config

        s.mss = c.get('greekMSS')
        s.latin_mss = c.get('latinMSS')
        if not s.is_greek:
            s.mss.extend(s.latin_mss)

        s.initVMap(s.maj)
        s.initVMap(s.ext)
        s.initXMap(s.tot_agr)
        s.initXMap(s.dst_agr)
        s.initXMap(s.tot_ext)
        s.initXMap(s.dst_ext)

        for addr in s.variantModel['addresses']:
            for vu in addr.variation_units:
                if vu.isSingular() or vu.isReferenceSingular('05'):
                    s.info('Excluding', vu.label)
                    continue
                elif s.is_greek and (vu.label in s.latinLayerCore or vu.label in s.latinLayerMulti or vu.isLatinOnly):
                    s.info('Excluding', vu.label)
                    continue

                s.info('Processing', vu.label)

                if not vu.startingAddress:
                    vu.startingAddress = addr

                extant_mss = vu.getExtantManuscripts()
                if s.is_greek:
                    extant_mss = list(set(extant_mss) - set(s.latin_mss))
                for ms in extant_mss:
                    s.ext[ms] = s.ext[ms] + 1

                elem_cmb = itertools.combinations(extant_mss, 2)
                for cmb in elem_cmb:
                    s.tot_ext[cmb[0]][cmb[1]] = s.tot_ext[cmb[0]][cmb[1]] + 1
                    s.tot_ext[cmb[1]][cmb[0]] = s.tot_ext[cmb[1]][cmb[0]] + 1

                for reading in vu.readings:
                    if not reading.manuscripts:
                        continue

                    is_maj = False
                    if reading.hasManuscript('35'):
                        is_maj = True

                    reading_mss = reading.manuscripts
                    if s.is_greek:
                        reading_mss = list(set(reading_mss) - set(s.latin_mss))
                    elem_cmb = itertools.combinations(reading_mss, 2)
                    for p_ms in reading_mss:
                        if is_maj:
                            s.maj[p_ms] = s.maj[p_ms] + 1
                            for cmb in elem_cmb:
                                s.tot_agr[cmb[0]][cmb[1]] = s.tot_agr[cmb[0]][cmb[1]] + 1
                                s.tot_agr[cmb[1]][cmb[0]] = s.tot_agr[cmb[1]][cmb[0]] + 1
                        else:
                            for s_ms in extant_mss:
                                if s_ms == p_ms:
                                    continue
                                s.dst_ext[p_ms][s_ms] = s.dst_ext[p_ms][s_ms] + 1
                            for cmb in elem_cmb:
                                s.dst_agr[cmb[0]][cmb[1]] = s.dst_agr[cmb[0]][cmb[1]] + 1
                                s.dst_agr[cmb[1]][cmb[0]] = s.dst_agr[cmb[1]][cmb[0]] + 1

    def initialize(s):
        c = s.config = Config('processor-config.json')
        s.info('Initializing grouper')

        if s.is_greek:
            s.latinLayerCore = c.get('latinLayerCoreVariants').split(u'|')
            s.latinLayerMulti = c.get('latinLayerMultiVariants').split(u'|')

        jsondata = ''
        jsonfile = c.get('finderFolder') + 'grouping-output-' + s.r_set + '.json'
        if os.path.exists(jsonfile):
            with open(jsonfile, 'r') as file:
                s.info('Loading saved grouper results from', jsonfile)
                jsondata = file.read().decode('utf-8')
                file.close()
            s.ms_results = json.loads(jsondata)

    def isInitialized(s):
        return True if s.ms_results else False

    def group(s):
        c = s.config = Config('processor-config.json')
        s.info('Grouping witnesses')

        if not s.isInitialized():
            if not s.variantModel:
                s.info('No variant model')
                return
            s.processReadings()
            s.computeRatios()

        s.writeOutput()

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info) 
