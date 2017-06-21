#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, argparse, urllib, subprocess, string, re, shutil, datetime, operator, json

from multiprocessing import Process, Lock

from object.jsonDecoder import *
from object.referenceManuscript import *
from object.referenceVariant import *

from utility.config import *
from utility.options import *

def callR(lock, rms, chapter, langCode):
    title = 'Mark ' + chapter + '-' + rms + langCode
    csvfile = chapter + '-' + rms + langCode + '.csv'

    p = ['C:\\Dev\\R\\R-3.3.2\\bin\\R.exe']
    p.append('--vanilla')
    p.append('--args')
    p.append('C:\\Data\\Workspace\\reading-processor\\r\\cluster-config.yml')
    p.append(title)
    p.append('C:\\Data\\Workspace\\reading-processor\\csv\\' + csvfile)
    p.append('<')
    p.append('C:\\Data\\Workspace\\reading-processor\\r\\cluster.R')
    p.append('>')
    p.append(title + '-out.txt')

    lock.acquire()
    print('running stats on', rms)
    print('command:', subprocess.list2cmdline(p))
    lock.release()

    proc = subprocess.Popen(p, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    lock.acquire()
    print out
    print err
    print ''
    lock.release()

class DiffAnalyzer:

    def __init__(s):
        s.chapter = ''
        s.variantModel = []

        s.comparisonMSS = []
        s.latinMSS = []
        s.nilExceptions = []
        s.refMS_IDs = []
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

    def generateVector(s, refMS, refVar, vu, reading, mss, nils, vars, vect):
        v = []
        for ms in getattr(refMS, mss):
            if not vu.getReadingForManuscript(ms):
                v.append('9')
                s.addNil(ms, getattr(refMS, nils))
            elif reading.hasManuscript(ms):
                v.append('1')
            else:
                v.append('0')

        refVar.__dict__[vect] = v
        tmp = getattr(refVar, vect)
        tmp = v
        getattr(refMS, vars).append(refVar)

    def writeSingular(s, refMS):
        c = s.config
        csvfile = c.get('csvFolder') + s.chapter + '-' + refMS.gaNum + 'SG' + '.csv'
        with open(csvfile, 'w+') as file:
            # write CSV header
            file.write((u'C1\tC2\tC3\tSEQ\tLayer\n').encode('utf-8'))

            disp_counter = 1
            for vu in refMS.singular:
                file.write((vu.label + u'\t' + vu.label + u'\t' + vu.label + u' ' + vu.getExcerpt(refMS.gaNum, '', True) + u'\t' + s.generateID(disp_counter) + u'\t4\n').encode('utf-8'))

                disp_counter = disp_counter + 1
            file.close()

    def writeCSV(s, refMS, sfx, mss, nils, vars, vect):
        c = s.config

        csvfile = c.get('csvFolder') + s.chapter + '-' + refMS.gaNum + sfx + '.csv'
        with open(csvfile, 'w+') as file:
            # number of nils allowed
            num_nils = len(refMS.__dict__[vars]) * 0.05
            nonnil_MSS = [m for m in refMS.__dict__[mss] if refMS.__dict__[nils][m] < num_nils or m in s.nilExceptions]

            # write CSV header
            file.write((u'C1\tC2\tC3\tSEQ\tLayer\t' + u'\t'.join(nonnil_MSS) + u'\n').encode('utf-8'))

            # write CSV content
            disp_counter = 1
            for var in refMS.__dict__[vars]:
                nonnil_vect = []
                witness_str = ''
                v_witnesses = []
                latin_counter = 0
                greek_counter = 0
                has35 = False
                for i, m in enumerate(refMS.__dict__[mss]):
                    if m in nonnil_MSS:
                        nonnil_vect.append(var.__dict__[vect][i])
                        if (var.__dict__[vect])[i] == '1':
                            if m[0] == 'V' or m[0] == 'v':
                                v_witnesses.append(m)
                                latin_counter = latin_counter + 1
                            else:
                                if len(witness_str) > 0:
                                    witness_str = witness_str + ' '
                                witness_str = witness_str + m
                                greek_counter = greek_counter + 1
                                if m == '35':
                                    has35 = True

                # is vect all zeroes or all ones (minus unattested cols)?
                if nonnil_vect.count('0') == len(nonnil_vect) - nonnil_vect.count('9') or nonnil_vect.count('1') == len(nonnil_vect) - nonnil_vect.count('9'):
                    continue

                # compute layer
                layer = 2
                if has35:
                    layer = 1
                elif latin_counter >= greek_counter and latin_counter > 2 and greek_counter <= 3:
                    layer = 3
                else:
                    if latin_counter >= greek_counter and latin_counter > 1 and greek_counter <= 2:
                        layer = 3
                    elif latin_counter >= greek_counter and latin_counter > 0 and greek_counter <= 1:
                        layer = 3

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

                # Debug layer assignment
                #s.info(witness_str, ', layer', str(layer), ', lcounter', str(latin_counter), ', gcounter', str(greek_counter))

                # zero 9's
                vct = []
                for val in nonnil_vect:
                    if val == '9':
                        vct.append('0')
                    else:
                        vct.append(val)

                file.write((var.shortLabel() + u'\t' + var.mediumLabel(witness_str) + u'\t' + var.longLabel(witness_str, nonnil_MSS) + u'\t' + s.generateID(disp_counter) + u'\t' + str(layer).decode('utf-8') + '\t' + u'\t'.join(vct) + u'\n').encode('utf-8'))

                disp_counter = disp_counter + 1
            file.close()

    def generateReferenceCSV(s):
        c = s.config
        s.info('')
        for rms in s.referenceMSS:
            s.info('generating CSVs for', rms.gaNum)

            # selG
            s.writeCSV(rms, 'G', 'selGrMSS', 'selGr_nils', 'sel_G', 'selGrVect')

            # selGL
            s.writeCSV(rms, 'GL', 'selMSS', 'sel_nils', 'sel_GL', 'selVect')

            # singular
            s.writeSingular(rms)

    def generateVariants(s):
        s.info('')
        for rms in s.refMS_IDs:
            s.info('generating variants for', rms)
            refMS = ReferenceManuscript(rms)

            refMS.allMSS = [m for m in s.variantModel['manuscripts'] if m <> rms]
            for ms in refMS.allMSS:
                refMS.all_nils[ms] = 0

            refMS.allGrMSS = [m for m in refMS.allMSS if m not in s.latinMSS]
            for ms in refMS.allGrMSS:
                refMS.allGr_nils[ms] = 0

            refMS.selMSS = [m for m in s.comparisonMSS if m <> rms]
            for ms in refMS.selMSS:
                refMS.sel_nils[ms] = 0

            refMS.selGrMSS = [m for m in refMS.selMSS if m not in s.latinMSS]
            for ms in refMS.selGrMSS:
                refMS.selGr_nils[ms] = 0

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

                        refVar = ReferenceVariant(vu, reading, rms)

                        # Readings with Greek and unambiguous Latin support
                        if vu.hasRetroversion:
                            s.generateVector(refMS, refVar, vu, reading, 'allMSS', 'all_nils', 'all_GL', 'allVect')

                            s.generateVector(refMS, refVar, vu, reading, 'selMSS', 'sel_nils', 'sel_GL', 'selVect')

                            s.generateVector(refMS, refVar, vu, reading, 'selGrMSS', 'selGr_nils', 'sel_G', 'selGrVect')
                        else:
                            s.generateVector(refMS, refVar, vu, reading, 'selGrMSS', 'selGr_nils', 'sel_G', 'selGrVect')
                            

            s.referenceMSS.append(refMS)

    def loadVariants(s, varfile):
        model = ''
        with open(varfile, 'r') as file:
            s.info('loading', varfile)
            model = file.read().decode('utf-8-sig') # Remove BOM
            model = model.encode('utf-8') # Reencode without BOM
            file.close()

        # Load JSON
        s.variantModel = json.loads(model, cls=ComplexDecoder)

    # "C:\Dev\R\R-3.3.2\bin\R.exe" --vanilla --args "C:\Data\Workspace\reading-processor\r\cluster-config.yml" "Mark 1-05 GL" "C:\Data\Workspace\reading-processor\csv\c01-05GL.csv" < "C:\Data\Workspace\reading-processor\r\cluster.R" > out-gl.txt
    def runStats(s):
        if __name__ == '__main__':
            lock = Lock()

            for rms in s.refMS_IDs:
                # Greek with Latin retroversion
                p1 = Process(target=callR, args=(lock, rms, s.chapter, 'GL')).start()

                # Greek-only
                p2 = Process(target=callR, args=(lock, rms, s.chapter, 'G')).start()

                p1.join()
                p2.join()
        else:
            s.info('exiting __name__ not equal to __main__')

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        # source files
        if o.file:
            file = o.file + '.json'
        else:
            file = c.get('variantFile')

        if o.chapter:
            s.chapter = o.chapter
            chapter = o.chapter + '/'
        else:
            chapter = c.get('variantChapter')
            s.chapter = chapter[:len(chapter) - 1]

        varfile = c.get('variantFolder') + chapter + file

        # reference MSS
        s.refMS_IDs = c.get('referenceMSS')

        # comparison MSS
        s.comparisonMSS = c.get('comparisonMSS')

        # latin MSS
        s.latinMSS = c.get('latinMSS')

        # MSS accepted with nils
        s.nilExceptions = c.get('nilExceptions')

        try:
            s.loadVariants(varfile)

            s.generateVariants()

            s.generateReferenceCSV()

            #s.runStats()
        except ValueError as e:
            print e
            print 'If loading JSON, try removing the UTF-8 BOM.'

        s.info('Done')

# Invoke via entry point
# diffAnalyzer.py -v -C [chapter] -f [filename minus suffix]
# diffAnalyzer.py -v -C c01 -f mark-01a-all
DiffAnalyzer().main(sys.argv[1:])
