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

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print info

    def generateID(s, n):
        strid = str(n)
        initial_length = len(strid)
        if initial_length > 3:
            return ''
        for i in range(1, 4 - initial_length):
            strid = '0' + strid
        return strid

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

            refMS.allMSS = [m for m in s.variantModel['manuscripts'] if m <> rms]
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

            file_D.write((u'C1\tC2\tC3\tSEQ\tLayer\tWitnesses\tExcerpt\t' + u'\t'.join(hdr) + u'\n').encode('utf-8'))

            d_layer = sorted(d_layer, cmp=sortVariations)

            for w in d_layer:
                file_D.write((w['reference'] + u'\t' + w['mediumLabel'] + u'\t' + w['description'] + u'\t' + w['sequence'] + u'\t2\t' + w['witnesses'] + u'\t' + w['excerpt'] + u'\t' + u'\t'.join(w['agreementVector']) + u'\n').encode('utf-8'))

            file_D.close()

        csvfile_DM = c.get('csvBoolFolder') + s.chapter + '-' + refMS.gaNum + 'DM.csv'
        with open(csvfile_DM, 'w+') as file_DM:
            hdr = []
            for m in getattr(refMS, mss):
                if m[0] <> 'V' and m[0] <> 'v':
                    hdr.append(m)

            file_DM.write((u'C1\tC2\tC3\tSEQ\tLayer\tWitnesses\tExcerpt\t' + u'\t'.join(hdr) + u'\n').encode('utf-8'))

            dm_layer = sorted(dm_layer, cmp=sortVariations)

            for w in dm_layer:
                file_DM.write((w['reference'] + u'\t' + w['mediumLabel'] + u'\t' + w['description'] + u'\t' + w['sequence'] + u'\t2\t' + w['witnesses'] + u'\t' + w['excerpt'] + u'\t' + u'\t'.join(w['agreementVector']) + u'\n').encode('utf-8'))

            file_DM.close()

    def writeCSV(s, refMS, langCode, mss, nils, vars, vect, d_layer, dm_layer):
        c = s.config

        # Two CSV files: one for all variants, another for D-layer variants
        csvfile_all = c.get('csvBoolFolder') + s.chapter + '-' + refMS.gaNum + langCode + '.csv'
        with open(csvfile_all, 'w+') as file_all:
            file_all.write((u'C1\tC2\tC3\tSEQ\tLayer\tWitnesses\tExcerpt\t' + u'\t'.join(getattr(refMS, mss)) + u'\n').encode('utf-8'))

            # write CSV content
            disp_counter = 1
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
                sequence = s.generateID(disp_counter)

                # construct vectors
                vct_all = []
                vct_D = []
                vct_DM = []
                for idx, val in enumerate(refms_vect):
                    # D variants
                    m = getattr(refMS, mss)[idx]
                    if m[0] <> 'V' and m[0] <> 'v' and m <> '35':
                        vct_D.append(val)

                    if m[0] <> 'V' and m[0] <> 'v':
                        vct_DM.append(val)

                    # All variants
                    vct_all.append(val)

                # D-variants CSV
                if layer == 1:
                    wrapperDM = {
                        'wrapped': var,
                        'reference': var.shortLabel(),
                        'sequence': sequence,
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
                        'sequence': sequence,
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
                        'sequence': sequence,
                        'witnesses': witness_str,
                        'excerpt': excerpt,
                        'mediumLabel': var.mediumLabel(witness_str),
                        'description': longLabel,
                        'languageCode': langCode,
                        'agreementVector': vct_DM
                    }
                    dm_layer.append(wrapperDM)

                # All-variants CSV
                file_all.write((var.shortLabel() + u'\t' + var.mediumLabel(witness_str) + u'\t' + longLabel + u'\t' + sequence + u'\t' + str(layer).decode('utf-8') + u'\t' + witness_str + u'\t' + excerpt + u'\t' + u'\t'.join(vct_all) + u'\n').encode('utf-8'))

                disp_counter = disp_counter + 1

            file_all.close()

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
