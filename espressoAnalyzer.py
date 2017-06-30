#! python3.6
# -*- coding: utf-8 -*-

import sys, os, subprocess

from utility.config import *
from utility.options import *

import pandas as pd
import numpy as np

class EspressoAnalyzer:

    def __init__(s):
        s.df = None
        s.mscols = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def loadCSV(s, filename):
        c = s.config
        o = s.options
        s.info('processing', filename)

        s.df = pd.read_csv(filename, sep='\t')

    def writePLA(s, basename):
        c = s.config
        s.mscols = ['x' + x for x in s.df.columns.values[1:-1]]

        nlines = []
        plines = []
        for ridx in range(0, s.df.shape[0]):
            row = s.df.iloc[ridx]
            out = s.df.iloc[ridx]['OUT']
            msrow = row[1:-1]
            line = ''
            for cidx in range(0, len(s.mscols)):
                col = s.mscols[cidx]
                line = line + str(msrow[cidx])
            line = line + ' ' + str(out) + '\n'

            if str(out) == '1':
                plines.append(line)
            elif str(out) == '0':
                nlines.append(line)

        posfile = c.get('csvBoolFolder') + basename + '-pos.pla'
        with open(posfile, 'w+') as pfile:
            pfile.write('.i ' + str(len(s.mscols)) + '\n')
            pfile.write('.o 1\n')
            pfile.write('.p ' + str(len(plines)) + '\n')
            pfile.write('.ilb ' + ' '.join(s.mscols) + '\n')
            pfile.write('.ob y0\n')
            pfile.write('.type fr\n')
            for line in plines:
                pfile.write(line)
            pfile.write('.e')
            pfile.close()

        negfile = c.get('csvBoolFolder') + basename + '-neg.pla'
        with open(negfile, 'w+') as nfile:
            nfile.write('.i ' + str(len(s.mscols)) + '\n')
            nfile.write('.o 1\n')
            nfile.write('.p ' + str(len(nlines)) + '\n')
            nfile.write('.ilb ' + ' '.join(s.mscols) + '\n')
            nfile.write('.ob y0\n')
            nfile.write('.type fr\n')
            for line in nlines:
                nfile.write(line)
            nfile.write('.e')
            nfile.close()

    def callEspresso(s, basename, slice):
        c = s.config
        infile = c.get('csvBoolFolder') + basename + '-' + slice + '.pla'
        outfile = c.get('csvBoolFolder') + basename + '-' + slice + '-out.pla'
        p = ['espresso.exe']
        p.append(infile)
        p.append('>')
        p.append(outfile)

        proc = subprocess.Popen(p, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        boolFile = None
        basename = ''
        if type(o) is CommandLine:
            boolFile = o.file + '.csv'
            basename = o.file
        else:
            boolFile = c.get('boolFile')
            basename = boolFile[:-4]

        if not boolFile:
            return

        boolPath = c.get('csvBoolFolder') + boolFile

        s.loadCSV(boolPath)
        s.writePLA(basename)
        s.callEspresso(basename, 'pos')
        s.callEspresso(basename, 'neg')

        s.info('Done')

# Invoke via entry point
# espressoAnalyzer.py -v -f [filename minus suffix]
# espressoAnalyzer.py -v -f test4
EspressoAnalyzer().main(sys.argv[1:])
