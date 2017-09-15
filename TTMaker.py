#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, json, re

from object.jsonDecoder import *
from object.rangeManager import *
from object.referenceManuscript import *
from object.referenceVariant import *
from object.util import *

from utility.options import *
from utility.config import *

class TTMaker:

    def __init__(s):
        s.range_id = ''
        s.variantModel = []
        s.referenceMSS = []
        s.refMS_IDs = []
        s.qcaSet = 'default'
        s.boolDir = ''

        s.qcaMSS = []
        s.booleanAggregates = []
        s.rangeMgr = None

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print info

    def addNil(s, ms, nils_map):
        nils = 1
        if nils_map.has_key(ms):
            nils = nils_map.get(ms) + 1
        nils_map[ms] = nils

    def generateVector(s, refMS, refVar, vu, reading, mss, nils, vars, vect, outcome):
        v = []
        for ms in getattr(refMS, mss):
            if ms == 'OUT':
                v.append(outcome)
                continue

            if not vu.getReadingForManuscript(ms):
                v.append('-')
                s.addNil(ms, getattr(refMS, nils))
            elif reading.hasManuscript(ms):
                v.append('1')
            else:
                v.append('0')

        refVar.__dict__[vect] = v
        getattr(refMS, vars).append(refVar)

    def generateVariants(s):
        c = s.config

        s.info('')
        num2alpha = dict(zip(range(1, 27), string.ascii_lowercase))
        for rms in s.refMS_IDs:
            s.info('generating variants for', rms)
            refMS = ReferenceManuscript(rms)

            refMS.allMSS = s.variantModel['manuscripts']
            if not 'OUT' in refMS.allMSS:
                refMS.allMSS.append('OUT')
            for ms in refMS.allMSS:
                refMS.all_nils[ms] = 0

            refMS.allGrMSS = [m for m in refMS.allMSS if m not in c.get('latinMSS')]
            if not 'OUT' in refMS.allGrMSS:
                refMS.allGrMSS.append('OUT')
            for ms in refMS.allGrMSS:
                refMS.allGr_nils[ms] = 0

            for addr in s.variantModel['addresses']:
                for vu in addr.variation_units:
                    if not vu.startingAddress:
                        vu.startingAddress = addr

                    if vu.isReferenceSingular(rms):
                        refMS.singular.append(vu)
                    elif not vu.isSingular():
                        reading = vu.getReadingForManuscript(rms)
                        if not reading:
                            continue

                        # generate vector for each non-singular reading
                        for ridx, rdg in enumerate(vu.readings):
                            # skip singular
                            if len(rdg.manuscripts) <= 1:
                                continue

                            refVar = ReferenceVariant(vu, rdg, rms)
                            refVar.reading_index = num2alpha[ridx + 1].decode('utf-8')

                            # supported by ref MS?
                            outcome = '0'
                            if rdg.getDisplayValue() == reading.getDisplayValue():
                                outcome = '1'

                            # Readings with Greek and unambiguous Latin support
                            if vu.hasRetroversion:
                                s.generateVector(refMS, refVar, vu, rdg, 'allMSS', 'all_nils', 'all_GL', 'allVect', outcome)
                            else:
                                s.generateVector(refMS, refVar, vu, rdg, 'allGrMSS', 'allGr_nils', 'all_G', 'allGrVect', outcome)

            s.referenceMSS.append(refMS)

    def getAggregatesForLangCode(s, langCode):
        aggrs = []
        for aggr in s.booleanAggregates:
            if langCode in aggr['langCodes']:
                aggrs.append(aggr)
        return aggrs

    def getAggregatesForLayer(s, aggregates, layer):
        aggrs = []
        for aggr in aggregates:
            if layer in aggr['layers']:
                aggrs.append(aggr)
        return aggrs

    def getAggregateForName(s, aggregates, name):
        for aggr in aggregates:
            if aggr['name'] == name:
                return aggr
        return None

    def getAggregatesHasMS(s, aggregates, ms):
        for aggr in aggregates:
            if ms in aggr['members']:
                return True
        return False

    def getAggregatesName(s, aggregates, ms):
        # MS allowed in only one aggregate!
        for aggr in aggregates:
            if ms in aggr['members']:
                return aggr['name']
        return ''

    def isAggregateName(s, aggregates, col):
        for aggr in aggregates:
            if col == aggr['name']:
                return True
        return False

    def writeHeader(s, file, ref_id, l_aggregates, incl_latin):
        c = s.config

        l_cols = ''
        qcaCols = [m for m in s.qcaMSS if m <> ref_id]
        for ms in qcaCols:
            if not incl_latin and (ms[:1] == 'V' or ms[:1] == 'v'):
                continue

            # MS can appear in only one aggregate,
            # but several MSS can appear in the same aggregate,
            # so consider each aggregate just once
            if s.getAggregatesHasMS(l_aggregates, ms):
                name = s.getAggregatesName(l_aggregates, ms)
                parts = l_cols.split('\t')
                if not name in parts: # Aggregate used?
                    if len(l_cols) > 0:
                        l_cols = l_cols + u'\t'
                    l_cols = l_cols + name
            else:
                if len(l_cols) > 0:
                    l_cols = l_cols + u'\t'
                l_cols = l_cols + ms

        # Affix OUT column
        l_cols = l_cols + '\tOUT'

        file.write((u'C1\tAggregate Support\tLayer\tWitnesses\tExcerpt\t' + l_cols + u'\n').encode('utf-8'))

        return l_cols

    def getValueForColumn(s, mss_vct, val_vct, col):
        for idx, ms in enumerate(mss_vct):
            if ms == col:
                return val_vct[idx]
        return '-'

    def computeAggregateValue(s, aggregates, mss_vct, val_vct, col, refms):
        aggr = s.getAggregateForName(aggregates, col)
        if aggr:
            ms_vals = ''
            occurs = 0
            for ms in aggr['members']:
                if ms == refms:
                    continue

                val = s.getValueForColumn(mss_vct, val_vct, ms)
                if val == '1':
                    if len(ms_vals) == 0:
                        ms_vals = col + u': ' + ms
                    else:
                        ms_vals = ms_vals + u', ' + ms
                        
                    occurs = occurs + 1

            # Clean up VL string
            if col == 'VL':
                ms_vals = re.sub(r'VL', '', ms_vals)
                ms_vals = 'VL' + ms_vals

            if occurs >= aggr['minOccurs']:
                return ('1', ms_vals )

        return ('0', '')

    def genAggregateVect(s, l_cols, l_aggregates, mss_vct, val_vct, refms):
        msval_str = ''
        out_vct = []
        parts = l_cols.split('\t')
        for col in parts:
            if s.isAggregateName(l_aggregates, col):
                result = s.computeAggregateValue(l_aggregates, mss_vct, val_vct, col, refms)
                val = result[0]

                if val == '1':
                    if len(msval_str) > 0:
                        msval_str = msval_str + '; '
                    msval_str = msval_str + result[1]
            else:
                val = s.getValueForColumn(mss_vct, val_vct, col)

            out_vct.append(val)

        return { 'msVals': msval_str, 'vect': out_vct}

    def writeVector(s, file, layer, agdat, ref, witness_str, excerpt):
        if agdat['vect'].count('0') != len(agdat['vect']) and agdat['vect'].count('1') != len(agdat['vect']):
            witness_str = re.sub(r' OUT', '', witness_str)
            file.write((ref + u'\t' + agdat['msVals'] + u'\t' + str(layer).decode('utf-8') + u'\t' + witness_str + u'\t' + excerpt + u'\t' + u'\t'.join(agdat['vect']) + u'\n').encode('utf-8'))

    def generateReferenceCSV(s):
        c = s.config
        s.info('')
        for rms in s.referenceMSS:
            s.info('generating truth tables for', rms.gaNum)

            d_layer = []
            m_layer = []
            l_cols = { 'layer_1': [], 'layer_2': [] }

            # selGL
            s.writeCSV(rms, 'GL', 'allMSS', 'all_nils', 'all_GL', 'allVect', d_layer, m_layer, l_cols)

            # selG
            s.writeCSV(rms, 'G', 'allGrMSS', 'allGr_nils', 'all_G', 'allGrVect', d_layer, m_layer, l_cols)

            s.writeLayers(rms, 'allMSS', d_layer, m_layer)

    def writeLayers(s, refMS, mss, d_layer, m_layer):
        c = s.config

        csvfile_D = s.boolDir + s.range_id + '-' + refMS.gaNum + 'D.csv'
        with open(csvfile_D, 'a+') as file_D:
            d_layer = sorted(d_layer, cmp=sortVariations)

            for w in d_layer:
                s.writeVector(file_D, w['layer'], w['aggregateData'], w['reference'], w['witnesses'], w['excerpt'])

            file_D.close()

        csvfile_M = s.boolDir + s.range_id + '-' + refMS.gaNum + 'M.csv'
        with open(csvfile_M, 'a+') as file_M:
            m_layer = sorted(m_layer, cmp=sortVariations)

            for w in m_layer:
                s.writeVector(file_M, w['layer'], w['aggregateData'], w['reference'], w['witnesses'], w['excerpt'])

            file_M.close()

    def writeCSV(s, refMS, langCode, mss, nils, vars, vect, d_layer, m_layer, l_cols):
        c = s.config

        aggregates = s.getAggregatesForLangCode(langCode)
        l1_aggregates = s.getAggregatesForLayer(aggregates, 1)
        l2_aggregates = s.getAggregatesForLayer(aggregates, 2)
        if langCode == 'GL':
            l3_aggregates = s.getAggregatesForLayer(aggregates, 3)

        file_Dgl = None
        file_L = None
        l1_cols = ''
        l2gl_cols = ''
        l2_cols = ''
        l3_cols = ''
        if langCode == 'GL': # GL must be called before G
            file_pref = s.boolDir + s.range_id + '-' + refMS.gaNum
            csvfile = file_pref + 'Dgl.csv'
            file_Dgl = open(csvfile, 'w+')
            l2gl_cols = s.writeHeader(file_Dgl, refMS.gaNum, l2_aggregates, True)

            csvfile = file_pref + 'L.csv'
            file_L = open(csvfile, 'w+')
            l3_cols = s.writeHeader(file_L, refMS.gaNum, l3_aggregates, True)

            csvfile = file_pref + 'D.csv'
            file_D = open(csvfile, 'w+')
            l_cols['layer_2'] = s.writeHeader(file_D, refMS.gaNum, l2_aggregates, False)
            if file_D: file_D.close()

            csvfile = file_pref + 'M.csv'
            file_M = open(csvfile, 'w+')
            l_cols['layer_1'] = s.writeHeader(file_M, refMS.gaNum, l1_aggregates, False)
            if file_M: file_M.close()

        for var in getattr(refMS, vars):
            refms_vect = []
            witness_str = ''
            v_witnesses = []
            latin_counter = 0
            greek_counter = 0
            has35 = False
            for i, m in enumerate(getattr(refMS, mss)):
                refms_vect.append(getattr(var, vect)[i])
                if (getattr(var, vect))[i] == '1':
                    if m[0] == 'V' or m[0] == 'v':
                        v_witnesses.append(m)
                        latin_counter = latin_counter + 1
                    else:
                        if len(witness_str) > 0:
                            witness_str = witness_str + ' '
                        witness_str = witness_str + m
                        greek_counter = greek_counter + 1
                        if m == '35': has35 = True

            # compute layer of ref MS reading
            layer = refMS.getLayer(var)

            # build witness string
            v_str = ''
            hasVulgate = False
            for m in v_witnesses:
                if m[0:2] == 'VL':
                    if len(v_str) > 0:
                        v_str = v_str + ' '
                    v_str = v_str + m[2:]
                elif m == 'vg':
                    hasVulgate = True

            if len(v_str) > 0:
                v_str = 'VL(' + v_str + ')'

            if hasVulgate:
                if len(v_str) > 0:
                    v_str = v_str + ' '
                v_str = v_str + 'V'

            if len(witness_str) > 0:
                if len(v_str) > 0:
                    witness_str = witness_str + ' ' + v_str
            else:
                if len(v_str) > 0:
                    witness_str = v_str

            # reading summary excerpt
            excerpt = var.variationUnit.getExcerpt(var.reading, witness_str, False)

            # construct vectors
            if layer == 1:
                agdat_M = s.genAggregateVect(l_cols['layer_1'], l1_aggregates, getattr(refMS, mss), getattr(var, vect), refMS.gaNum)

            if layer == 2:
                agdat_D = s.genAggregateVect(l_cols['layer_2'], l2_aggregates, getattr(refMS, mss), getattr(var, vect), refMS.gaNum)

            # D layer CSV with Latin witnesses
            if langCode == 'GL' and layer == 2:
                # Generate readings vector with aggregates
                agdat_Dgl = s.genAggregateVect(l2gl_cols, l2_aggregates, getattr(refMS, mss), getattr(var, vect), refMS.gaNum)

                s.writeVector(file_Dgl, layer, agdat_Dgl, var.shortLabel(), witness_str, excerpt)

            # Latin layer CSV
            if langCode == 'GL' and layer == 3:
                # Generate readings vector with aggregates
                agdat_L = s.genAggregateVect(l3_cols, l3_aggregates, getattr(refMS, mss), getattr(var, vect), refMS.gaNum)

                s.writeVector(file_L, layer, agdat_L, var.shortLabel(), witness_str, excerpt)

            # D-variants CSV
            if layer == 1:
                wrapperM = {
                    'wrapped': var, # used for sort
                    'reference': var.shortLabel(),
                    'layer': str(layer).decode('utf-8'),
                    'witnesses': witness_str,
                    'excerpt': excerpt,
                    'aggregateData': agdat_M
                }
                m_layer.append(wrapperM)
            elif layer == 2:
                wrapperD = {
                    'wrapped': var, # used for sort
                    'reference': var.shortLabel(),
                    'layer': str(layer).decode('utf-8'),
                    'witnesses': witness_str,
                    'excerpt': excerpt,
                    'aggregateData': agdat_D
                }
                d_layer.append(wrapperD)

        if file_Dgl:
            file_Dgl.close()
        if file_L:
            file_L.close()

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

        if o.qcaSet:
            s.qcaSet = o.qcaSet
        else:
            s.qcaSet = c.get('qcaSet')

        # load variant data
        s.rangeMgr = RangeManager()
        s.rangeMgr.load()

        s.variantModel = s.rangeMgr.getModel(s.range_id)

        s.qcaMSS = s.config.get('qcaSets')[s.qcaSet]['qcaMSS']
        s.booleanAggregates = s.config.get('qcaSets')[s.qcaSet]['aggregates']

        # ensure output directory exists
        s.boolDir = c.get('csvBoolFolder') + s.qcaSet + '/'
        if not os.path.exists(s.boolDir):
            os.makedirs(s.boolDir)

        try:
            s.generateVariants()

            s.generateReferenceCSV()
        except ValueError as e:
            print e
            print 'If loading JSON, try removing the UTF-8 BOM.'

        s.info('Done')

# Invoke via entry point
# TTMaker.py -v -a c15-16 -R 05
TTMaker().main(sys.argv[1:])
