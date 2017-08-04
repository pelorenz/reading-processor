#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, argparse, urllib, subprocess, string, re, shutil, datetime, operator, json

from multiprocessing import Process, Lock

from object.referenceManuscript import *
from object.referenceVariant import *
from object.util import *

from utility.config import *
from utility.env import *

def callCormat(lock, rms, chapter, langCode):
    title = 'Mark ' + chapter[1:] + '-' + rms + langCode
    csvfile = chapter + '-' + rms + langCode + '.csv'
    singfile = chapter + '-' + rms + 'SG.csv'

    p = ['C:\\Dev\\R\\R-3.3.2\\bin\\R.exe']
    p.append('--vanilla')
    p.append('--args')
    p.append('C:\\Data\\Workspace\\reading-processor\\r\\cluster-config.yml')
    p.append(title)
    p.append('C:\\Data\\Workspace\\reading-processor\\csv\\' + csvfile)
    p.append('<')
    p.append('C:\\Data\\Workspace\\reading-processor\\r\\cormat.R')
    p.append('>')
    p.append(title + '-out-cormat.txt')

    #DEBUG: print('command:', subprocess.list2cmdline(p))
    proc = subprocess.Popen(p, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    lock.acquire()
    print out
    print err
    print ''
    lock.release()

def callClust(lock, rms, chapter, langCode, nclusts):
    title = 'Mark ' + chapter[1:] + '-' + rms + langCode
    csvfile = chapter + '-' + rms + langCode + '.csv'
    singfile = chapter + '-' + rms + 'SG.csv'

    p = ['C:\\Dev\\R\\R-3.3.2\\bin\\R.exe']
    p.append('--vanilla')
    p.append('--args')
    p.append('C:\\Data\\Workspace\\reading-processor\\r\\cluster-config.yml')
    p.append(title)
    p.append('C:\\Data\\Workspace\\reading-processor\\csv\\' + csvfile)
    p.append('C:\\Data\\Workspace\\reading-processor\\csv\\' + singfile)
    p.append(str(nclusts))
    p.append(langCode)
    p.append('<')
    p.append('C:\\Data\\Workspace\\reading-processor\\r\\cluster.R')
    p.append('>')
    p.append(title + '-out-clust.txt')

    #DEBUG: print('command:', subprocess.list2cmdline(p))
    proc = subprocess.Popen(p, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    lock.acquire()
    print out
    print err
    print ''
    lock.release()

def callDistrib(lock, rms, chapter, langCode):
    title = 'Mark ' + chapter[1:] + '-' + rms + langCode
    if '0' in chapter:
        label = 'Mark ' + chapter[2:]
    else:
        label = 'Mark ' + chapter[1:]
    csvfile = chapter + '-' + rms + langCode + '.csv'
    singfile = chapter + '-' + rms + 'SG.csv'

    p = ['C:\\Dev\\R\\R-3.3.2\\bin\\R.exe']
    p.append('--vanilla')
    p.append('--args')
    p.append('C:\\Data\\Workspace\\reading-processor\\r\\cluster-config.yml')
    p.append(title)
    p.append(label)
    p.append('C:\\Data\\Workspace\\reading-processor\\csv\\' + csvfile)
    p.append('C:\\Data\\Workspace\\reading-processor\\csv\\' + singfile)
    p.append('<')
    p.append('C:\\Data\\Workspace\\reading-processor\\r\\distrib.R')
    p.append('>')
    p.append(title + '-out-distrib.txt')

    #DEBUG: print('command:', subprocess.list2cmdline(p))
    proc = subprocess.Popen(p, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    lock.acquire()
    print out
    print err
    print ''
    lock.release()

class Analyzer:

    def __init__(s):
        s.chapter = ''
        s.variantModel = []

        s.referenceMSS = []
        s.minClusters = 2
        s.maxClusters = 2

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
        getattr(refMS, vars).append(refVar)

    def writeSingular(s, refMS):
        c = s.config
        csvfile = c.get('csvFolder') + s.chapter + '-' + refMS.gaNum + 'SG' + '.csv'
        with open(csvfile, 'w+') as file:
            # write CSV header
            file.write((u'C1\tC2\tC3\tSEQ\tLayer\tExcerpt\n').encode('utf-8'))

            disp_counter = 1
            for vu in refMS.singular:
                excerpt = vu.getExcerpt(vu.getReadingForManuscript(refMS.gaNum), '', True)
                file.write((vu.label + u'\t' + vu.label + u'\t' + vu.label + u' ' + excerpt + u'\t' + excerpt + u'\t' + s.generateID(disp_counter) + u'\t4\n').encode('utf-8'))

                disp_counter = disp_counter + 1
            file.close()

    def writeCSV(s, refMS, langCode, mss, nils, vars, vect, layersMap, variantsMap, witnessesMap):
        c = s.config

        # Two CSV files: one for all variants, another for D-layer variants
        csvfile_all = c.get('csvFolder') + s.chapter + '-' + refMS.gaNum + langCode + '.csv'
        csvfile_D = c.get('csvFolder') + s.chapter + '-' + refMS.gaNum + 'D.csv'
        with open(csvfile_all, 'w+') as file_all:
            fmode = 'w+' if langCode == 'GL' else 'a+'
            with open(csvfile_D, fmode) as file_D:
                # number of nils allowed
                num_nils = len(refMS.__dict__[vars]) * 0.05
                nonnil_MSS = [m for m in refMS.__dict__[mss] if refMS.__dict__[nils][m] < num_nils or m in s.env.nilExceptions]

                # write header for all-variant CSV
                file_all.write((u'C1\tC2\tC3\tSEQ\tLayer\tWitnesses\tExcerpt\t' + u'\t'.join(nonnil_MSS) + u'\n').encode('utf-8'))

                # write header for D-variant CSV first time only
                if langCode == 'GL':
                    hdr = []
                    for m in nonnil_MSS:
                        if m[0] <> 'V' and m[0] <> 'v' and m <> '35':
                            hdr.append(m)

                    file_D.write((u'C1\tC2\tC3\tSEQ\tLayer\tWitnesses\tExcerpt\t' + u'\t'.join(hdr) + u'\n').encode('utf-8'))

                # write CSV content
                disp_counter = 1
                for var in refMS.__dict__[vars]:
                    nonnil_vect = []
                    witness_str = ''
                    v_witnesses = []
                    latin_counter = 0
                    greek_counter = 0
                    has35 = has03 = has05 = has032 = has038 = has28 = has565 = has700 = has788 = False
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
                                    if m == '35': has35 = True
                                    if m == '03': has03 = True
                                    if m == '05': has05 = True
                                    if m == '032': has032 = True
                                    if m == '038': has038 = True
                                    if m == '28': has28 = True
                                    if m == '788': has565 = True
                                    if m == '700': has700 = True
                                    if m == '788': has788 = True

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

                    # compute D sublayer
                    d_layer = 1
                    if has03 and not (has038 or has28 or has565 or has700 or has788) and not (has032 or has05):
                        d_layer = 2
                    elif (has032 or has05) and not (has038 or has28 or has565 or has700 or has788) and not has03:
                        d_layer = 4
                    else:
                        if (has038 or has28 or has565 or has700 or has788) and not has03 and not (has032 or has05):
                            d_layer = 3

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

                    rdg = var.variationUnit.getReadingForManuscript(refMS.gaNum)
                    excerpt = var.variationUnit.getExcerpt(rdg, witness_str, False)
                    longLabel = var.longLabel(rdg, witness_str, nonnil_MSS)
                    sequence = s.generateID(disp_counter)

                    # assign to layer (variant might already exist in layer!)
                    label = var.variationUnit.label
                    if not variantsMap.has_key(label):
                        wrapper = {
                            'wrapped': var,
                            'sequence': sequence,
                            'witnesses': witness_str,
                            'excerpt': excerpt,
                            'description': longLabel,
                            'languageCode': langCode
                        }
                        if (refMS.gaNum == '05' and witness_str == 'VL(5)'):
                            layer = 4 # move VL(5) readings to singular layer
                        layersMap[layer].append(wrapper)
                        variantsMap[label] = layer

                        # increment witness occurrences for layer
                        for i, m in enumerate(refMS.__dict__[mss]):
                            if m in nonnil_MSS:
                                mkey = m
                                if mkey[:1].isdigit():
                                    mkey = 'X' + mkey
                                if not witnessesMap[layer].has_key(mkey):
                                    witnessesMap[layer][mkey] = { "id": mkey, "occurrences": "0" }
                                if (var.__dict__[vect])[i] == '1':
                                    witnessesMap[layer][mkey]['occurrences'] = str(int(witnessesMap[layer][mkey]['occurrences']) + 1).decode('utf-8')

                    # Debug layer assignment
                    #s.info(witness_str, ', layer', str(layer), ', lcounter', str(latin_counter), ', gcounter', str(greek_counter))

                    # zero 9's
                    vct_all = []
                    vct_D = []
                    for idx, val in enumerate(nonnil_vect):
                        # D variants
                        m = nonnil_MSS[idx]
                        if m[0] <> 'V' and m[0] <> 'v' and m <> '35':
                            if val == '9':
                                vct_D.append('0')
                            else:
                                vct_D.append(val)

                        # All variants
                        if val == '9':
                            vct_all.append('0')
                        else:
                            vct_all.append(val)

                    # D-variants CSV
                    if layer == 2:
                        # Truncate Latin witnesses

                        file_D.write((var.shortLabel() + u'\t' + var.mediumLabel(witness_str) + u'\t' + longLabel + u'\t' + sequence + u'\t' + str(d_layer).decode('utf-8') + '\t' + witness_str + u'\t' + excerpt + u'\t' + u'\t'.join(vct_D) + u'\n').encode('utf-8'))

                    # All-variants CSV
                    file_all.write((var.shortLabel() + u'\t' + var.mediumLabel(witness_str) + u'\t' + longLabel + u'\t' + sequence + u'\t' + str(layer).decode('utf-8') + '\t' + witness_str + u'\t' + excerpt + u'\t' + u'\t'.join(vct_all) + u'\n').encode('utf-8'))

                    disp_counter = disp_counter + 1

                file_D.close()
                file_all.close()

    def writeLayers(s, rms, layersMap, witnessesMap):
        c = s.config

        j_layers = { 'clusters': [] }
        for idx in range(1, 4):
            witnessList = []
            # prepare witness list from witness map
            for key, value in witnessesMap[idx].iteritems():
                witnessList.append(value)

            j_layer = { 
              'index': str(idx).decode('utf-8'),
              'size': str(len(layersMap[idx])).decode('utf-8'),
              'witnesses': witnessList,
              'readings': []
            }

            # sort variatons
            sorted_variations = sorted(layersMap[idx], cmp=sortVariations)

            # create readings
            for var in sorted_variations:
                j_var = {
                    'reference': var['wrapped'].variationUnit.label,
                    'languageCode': var['languageCode'],
                    'sequence': var['sequence'],
                    'layer': str(idx).decode('utf-8'),
                    'witnesses': var['witnesses'],
                    'excerpt': var['excerpt'],
                    'description': var['description']
                }
                j_layer['readings'].append(j_var)

            j_layers['clusters'].append(j_layer)

        j_layer = { 
          'index': '4',
          'witnesses': [],
          'readings': []
        }

        # create singular readings
        disp_counter = 1
        for vu in rms.singular:
            excerpt = vu.getExcerpt(vu.getReadingForManuscript(rms.gaNum), '', True)
            j_var = {
                'reference': vu.label,
                'languageCode': 'S',
                'sequence': s.generateID(disp_counter),
                'layer': '4',
                'witnesses': '',
                'excerpt': excerpt,
                'description': vu.label + u' ' + excerpt
            }
            j_layer['readings'].append(j_var)

            disp_counter = disp_counter + 1

        # append singular readings with VL(5)
        sorted_variations = sorted(layersMap[4], cmp=sortVariations)

        # create readings
        for var in sorted_variations:
            j_var = {
                'reference': var['wrapped'].variationUnit.label,
                'languageCode': var['languageCode'],
                'sequence': var['sequence'],
                'layer': '4',
                'witnesses': var['witnesses'],
                'excerpt': var['excerpt'],
                'description': var['description']
            }
            j_layer['readings'].append(j_var)

        j_layer['size'] = str(len(rms.singular) + len(sorted_variations)).decode('utf-8')
        j_layers['clusters'].append(j_layer)

        jsonfile = c.get('layersFolder') + 'Mark ' + s.chapter[1:] + '-' + rms.gaNum + '.json'
        with open(jsonfile, 'w+') as file:
            jsonstr = json.dumps(j_layers, ensure_ascii=False)
            file.write(jsonstr.encode('utf-8'))
            file.close()

    def generateReferenceCSV(s):
        c = s.config
        s.info('')
        for rms in s.referenceMSS:
            s.info('generating CSVs for', rms.gaNum)

            # variants keyed by layer
            layersMap = {}
            layersMap[1] = []
            layersMap[2] = []
            layersMap[3] = []
            layersMap[4] = []

            # layers keyed by variant label
            variantsMap = {}

            # map of witness occurrences keyed by layer
            witnessesMap = {}
            witnessesMap[1] = {}
            witnessesMap[2] = {}
            witnessesMap[3] = {}
            witnessesMap[4] = {}

            # selGL
            s.writeCSV(rms, 'GL', 'selMSS', 'sel_nils', 'sel_GL', 'selVect', layersMap, variantsMap, witnessesMap)

            # selG
            s.writeCSV(rms, 'G', 'selGrMSS', 'selGr_nils', 'sel_G', 'selGrVect', layersMap, variantsMap, witnessesMap)

            # singular
            s.writeSingular(rms)

            # write layer JSON
            s.writeLayers(rms, layersMap, witnessesMap)

    def generateVariants(s):
        s.info('')
        for rms in s.env.refMS_IDs:
            s.info('generating variants for', rms)
            refMS = ReferenceManuscript(rms)

            refMS.allMSS = [m for m in s.variantModel['manuscripts'] if m <> rms]
            for ms in refMS.allMSS:
                refMS.all_nils[ms] = 0

            refMS.allGrMSS = [m for m in refMS.allMSS if m not in s.env.latinMSS]
            for ms in refMS.allGrMSS:
                refMS.allGr_nils[ms] = 0

            refMS.selMSS = [m for m in s.env.comparisonMSS if m <> rms]
            for ms in refMS.selMSS:
                refMS.sel_nils[ms] = 0

            refMS.selGrMSS = [m for m in refMS.selMSS if m not in s.env.latinMSS]
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
                            s.generateVector(refMS, refVar, vu, reading, 'selGrMSS', 'selGr_nils', 'sel_G', 'selGrVect')

                            s.generateVector(refMS, refVar, vu, reading, 'selMSS', 'sel_nils', 'sel_GL', 'selVect')
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
        __name__ = '__main__'
        if __name__ == '__main__':
            lock = Lock()
            procs = []
            for rms in s.env.refMS_IDs:
                # Correlation, similarity, and dissimilarity matrices
                procs.append(Process(target=callCormat, args=(lock, rms, s.chapter, 'GL')))
                procs.append(Process(target=callCormat, args=(lock, rms, s.chapter, 'G')))

                # Distributions for Greek with Latin retroversion
                procs.append(Process(target=callDistrib, args=(lock, rms, s.chapter, 'GL')))

                for p in procs:
                    p.start()

                for p in procs:
                    p.join()

                for n in range(s.minClusters, s.maxClusters + 1):
                    procs = []

                    # D layer
                    if rms == '05' or rms == '032':
                        procs.append(Process(target=callClust, args=(lock, rms, s.chapter, 'D', n)))

                    # Greek with Latin retroversion clustering
                    procs.append(Process(target=callClust, args=(lock, rms, s.chapter, 'GL', n)))

                    # Greek-only clustering
                    procs.append(Process(target=callClust, args=(lock, rms, s.chapter, 'G', n)))

                    for p in procs:
                        p.start()

                    for p in procs:
                        p.join()

        else:
            s.info('exiting __name__ not equal to __main__')

    def analyze(s, chapter, inputfile, refMSS):
        c = s.config = Config('processor-config.json')

        s.info('Calling analysis with chapter', chapter, 'and input file', inputfile)
        s.info('Reference MSS', refMSS)

        s.env = Env(c, {'chapter': chapter, 'inputfile': inputfile, 'refMSS_IDs': refMSS})

        s.chapter = s.env.chapter()
        s.variantModel = s.env.loadVariants(s.env.varFile())

        # Numbers of clusters
        s.minClusters = c.get('minClusters')
        s.maxClusters = c.get('maxClusters')

        try:
            s.generateVariants()

            s.generateReferenceCSV()

            s.runStats()
        except ValueError as e:
            print e
            print 'If loading JSON, try removing the UTF-8 BOM.'

        s.info('Done')
