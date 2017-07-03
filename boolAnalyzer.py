#! python2.7
# -*- coding: utf-8 -*-

from utility.options import *

#########################
# BEGIN analyzer

import sys, os, string

from object.referenceManuscript import *
from object.referenceVariant import *
from object.util import *

from utility.config import *
from utility.env import *

class BoolAnalyzer:

    def __init__(s):
        s.chapter = ''
        s.variantModel = []
        s.referenceMSS = []

        s.qcaMSS = []
        s.booleanAggregates = []

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
        s.info('')
        num2alpha = dict(zip(range(1, 27), string.ascii_lowercase))
        for rms in s.env.refMS_IDs:
            s.info('generating variants for', rms)
            refMS = ReferenceManuscript(rms)

            refMS.allMSS = s.variantModel['manuscripts']
            if not 'OUT' in refMS.allMSS:
                refMS.allMSS.append('OUT')
            for ms in refMS.allMSS:
                refMS.all_nils[ms] = 0

            refMS.allGrMSS = [m for m in refMS.allMSS if m not in s.env.latinMSS]
            if not 'OUT' in refMS.allGrMSS:
                refMS.allGrMSS.append('OUT')
            for ms in refMS.allGrMSS:
                refMS.allGr_nils[ms] = 0

            for addr in s.variantModel['addresses']:
                for vu in addr.variationUnits:
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

    def generateReferenceCSV(s):
        c = s.config
        s.info('')
        for rms in s.referenceMSS:
            s.info('generating CSVs for', rms.gaNum)

            d_layer = []
            dm_layer = []

            # selGL
            s.writeCSV(rms, 'GL', 'allMSS', 'all_nils', 'all_GL', 'allVect', d_layer, dm_layer)

            # selG
            s.writeCSV(rms, 'G', 'allGrMSS', 'allGr_nils', 'all_G', 'allGrVect', d_layer, dm_layer)

            s.writeLayers(rms, 'allMSS', d_layer, dm_layer)

    def writeLayers(s, refMS, mss, d_layer, dm_layer):
        c = s.config

        csvfile_D = c.get('csvBoolFolder') + s.chapter + '-' + refMS.gaNum + 'D.csv'
        with open(csvfile_D, 'w+') as file_D:
            hdr = []
            for m in getattr(refMS, mss):
                if m[0] <> 'V' and m[0] <> 'v' and m <> '35':
                    hdr.append(m)

            file_D.write((u'C1\tAggregate Support\tLayer\tWitnesses\tExcerpt\t' + u'\t'.join(hdr) + u'\n').encode('utf-8'))

            d_layer = sorted(d_layer, cmp=sortVariations)

            for w in d_layer:
                file_D.write((w['reference'] + u'\t' + w['layer'] + u'\t' + w['witnesses'] + u'\t' + w['excerpt'] + u'\t' + u'\t'.join(w['agreementVector']) + u'\n').encode('utf-8'))

            file_D.close()

        csvfile_DM = c.get('csvBoolFolder') + s.chapter + '-' + refMS.gaNum + 'DM.csv'
        with open(csvfile_DM, 'w+') as file_DM:
            hdr = []
            for m in getattr(refMS, mss):
                if m[0] <> 'V' and m[0] <> 'v':
                    hdr.append(m)

            file_DM.write((u'C1\tAggregate Support\tLayer\tWitnesses\tExcerpt\t' + u'\t'.join(hdr) + u'\n').encode('utf-8'))

            dm_layer = sorted(dm_layer, cmp=sortVariations)

            for w in dm_layer:
                file_DM.write((w['reference'] + u'\t' + w['layer'] + u'\t' + w['witnesses'] + u'\t' + w['excerpt'] + u'\t' + u'\t'.join(w['agreementVector']) + u'\n').encode('utf-8'))

            file_DM.close()

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

    def getValueForColumn(s, mss_vct, val_vct, col):
        for idx, ms in enumerate(mss_vct):
            if ms == col:
                return val_vct[idx]
        return '-'

    def computeAggregateValue(s, aggregates, mss_vct, val_vct, col):
        aggr = s.getAggregateForName(aggregates, col)
        if aggr:
            ms_vals = ''
            occurs = 0
            for ms in aggr['members']:
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

    def genAggregateVect(s, l_cols, l_aggregates, mss_vct, val_vct, result_vct):
        msval_str = ''
        parts = l_cols.split('\t')
        for col in parts:
            if s.isAggregateName(l_aggregates, col):
                result = s.computeAggregateValue(l_aggregates, mss_vct, val_vct, col)
                val = result[0]

                if val == '1':
                    if len(msval_str) > 0:
                        msval_str = msval_str + '; '
                    msval_str = msval_str + result[1]
            else:
                val = s.getValueForColumn(mss_vct, val_vct, col)
            
            result_vct.append(val)

        return msval_str

    def writeCSV(s, refMS, langCode, mss, nils, vars, vect, d_layer, dm_layer):
        c = s.config

        aggregates = s.getAggregatesForLangCode(langCode)
        l2_aggregates = s.getAggregatesForLayer(aggregates, 2)
        l3_aggregates = s.getAggregatesForLayer(aggregates, 3)

        file_Dgl = None
        file_L = None
        l2_cols = ''
        l3_cols = ''
        qcaCols = [m for m in s.qcaMSS if m <> refMS.gaNum]
        if langCode == 'GL':
            for ms in qcaCols:
                # MS can appear in only one aggregate,
                # but several MSS can appear in the same aggregate,
                # so consider each aggregate just once
                if s.getAggregatesHasMS(l2_aggregates, ms):
                    name = s.getAggregatesName(l2_aggregates, ms)
                    parts = l2_cols.split('\t')
                    if not name in parts: # Aggregate used?
                        if len(l2_cols) > 0:
                            l2_cols = l2_cols + u'\t'
                        l2_cols = l2_cols + name
                else:
                    if len(l2_cols) > 0:
                        l2_cols = l2_cols + u'\t'
                    l2_cols = l2_cols + ms

                if s.getAggregatesHasMS(l3_aggregates, ms):
                    name = s.getAggregatesName(l3_aggregates, ms)
                    parts = l3_cols.split('\t')
                    if not name in parts: # Aggregate used?
                        if len(l3_cols) > 0:
                            l3_cols = l3_cols + u'\t'
                        l3_cols = l3_cols + name
                else:
                    if len(l3_cols) > 0:
                        l3_cols = l3_cols + u'\t'
                    l3_cols = l3_cols + ms

            # Affix OUT column
            l2_cols = l2_cols + '\t' + refMS.gaNum
            l3_cols = l3_cols + '\t' + refMS.gaNum

            csvfile_Dgl = c.get('csvBoolFolder') + s.chapter + '-' + refMS.gaNum + 'Dgl.csv'
            file_Dgl = open(csvfile_Dgl, 'w+')
            file_Dgl.write((u'C1\tAggregate Support\tLayer\tWitnesses\tExcerpt\t' + l2_cols + u'\n').encode('utf-8'))

            csvfile_L = c.get('csvBoolFolder') + s.chapter + '-' + refMS.gaNum + 'L.csv'
            file_L = open(csvfile_L, 'w+')
            file_L.write((u'C1\tAggregate Support\tLayer\tWitnesses\tExcerpt\t' + l3_cols + u'\n').encode('utf-8'))

        csvfile_all = c.get('csvBoolFolder') + s.chapter + '-' + refMS.gaNum + langCode + '.csv'
        with open(csvfile_all, 'w+') as file_all:
            file_all.write((u'C1\tAggregate Support\tLayer\tWitnesses\tExcerpt\t' + u'\t'.join(getattr(refMS, mss)) + u'\n').encode('utf-8'))

            # write CSV content
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

                # is vect all zeroes or all ones (minus unattested cols)?
                if refms_vect.count('0') == len(refms_vect) - refms_vect.count('9') or refms_vect.count('1') == len(refms_vect) - refms_vect.count('9'):
                    continue

                # compute layer of ref MS reading
                layer = refMS.getLayer(var)

                # group VL witnesses
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

                excerpt = var.variationUnit.getExcerpt(var.reading, witness_str, False)
                longLabel = var.longLabel(var.reading, witness_str, getattr(refMS, mss))

                # construct vectors
                vct_all = []
                vct_D = []
                vct_Dgl = []
                vct_DM = []
                vct_L = []
                for idx, val in enumerate(refms_vect):
                    # D variants
                    m = getattr(refMS, mss)[idx]
                    if m[0] <> 'V' and m[0] <> 'v' and m <> '35':
                        vct_D.append(val)

                    if m[0] <> 'V' and m[0] <> 'v':
                        vct_DM.append(val)

                    # All variants
                    vct_all.append(val)

                # Generate D-GL readings vector with aggregates
                aggMSVals_Dgl = s.genAggregateVect(l2_cols, l2_aggregates, getattr(refMS, mss), getattr(var, vect), vct_Dgl)

                # Generate L-GL readings vector with aggregates
                aggMSVals_L = s.genAggregateVect(l3_cols, l3_aggregates, getattr(refMS, mss), getattr(var, vect), vct_L)

                # D-variants CSV
                if layer == 1:
                    wrapperDM = {
                        'wrapped': var,
                        'reference': var.shortLabel(),
                        'layer': str(layer).decode('utf-8'),
                        'witnesses': witness_str,
                        'excerpt': excerpt,
                        'mediumLabel': var.mediumLabel(witness_str),
                        'description': longLabel,
                        'languageCode': langCode,
                        'agreementVector': vct_DM
                    }
                    dm_layer.append(wrapperDM)
                elif layer == 2:
                    # Truncate Latin witnesses
                    wrapperD = {
                        'wrapped': var,
                        'reference': var.shortLabel(),
                        'layer': str(layer).decode('utf-8'),
                        'witnesses': witness_str,
                        'excerpt': excerpt,
                        'mediumLabel': var.mediumLabel(witness_str),
                        'description': longLabel,
                        'languageCode': langCode,
                        'agreementVector': vct_D
                    }
                    d_layer.append(wrapperD)

                    wrapperDM = {
                        'wrapped': var,
                        'reference': var.shortLabel(),
                        'layer': str(layer).decode('utf-8'),
                        'witnesses': witness_str,
                        'excerpt': excerpt,
                        'mediumLabel': var.mediumLabel(witness_str),
                        'description': longLabel,
                        'languageCode': langCode,
                        'agreementVector': vct_DM
                    }
                    dm_layer.append(wrapperDM)

                # D layer CSV with Latin witnesses
                if file_Dgl and layer == 2:
                    file_Dgl.write((var.shortLabel() + u'\t' + aggMSVals_Dgl + u'\t' + str(layer).decode('utf-8') + u'\t' + witness_str + u'\t' + excerpt + u'\t' + u'\t'.join(vct_Dgl) + u'\n').encode('utf-8'))

                # Latin layer CSV
                if file_L and layer == 3:
                    file_L.write((var.shortLabel() + u'\t' + aggMSVals_L + u'\t' + str(layer).decode('utf-8') + u'\t' + witness_str + u'\t' + excerpt + u'\t' + u'\t'.join(vct_L) + u'\n').encode('utf-8'))

                # All-variants CSV
                file_all.write((var.shortLabel() + u'\t\t' + str(layer).decode('utf-8') + u'\t' + witness_str + u'\t' + excerpt + u'\t' + u'\t'.join(vct_all) + u'\n').encode('utf-8'))

            file_all.close()
            if file_Dgl:
                file_Dgl.close()
            if file_L:
                file_L.close()

# END analyzer
#########################

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        s.env = Env(s.config, s.options)

        s.chapter = s.env.chapter()
        varfile = s.env.varFile()
        s.variantModel = s.env.loadVariants(varfile)
        s.info('loading', varfile)

        s.qcaMSS = s.config.get('qcaMSS')
        s.booleanAggregates = s.config.get('booleanAggregates')

        try:
            s.generateVariants()

            s.generateReferenceCSV()

            #s.runStats()
        except ValueError as e:
            print e
            print 'If loading JSON, try removing the UTF-8 BOM.'

        s.info('Done')

# Invoke via entry point
# boolAnalyzer.py -v -C [chapter] -f [filename minus suffix]
# boolAnalyzer.py -v -C c01 -f mark-01a-all
BoolAnalyzer().main(sys.argv[1:])
