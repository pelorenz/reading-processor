#! python3.6
# -*- coding: utf-8 -*-

import sys, os, string

from object.util import *

from utility.config import *
from utility.options import *

import pandas as pd
import numpy as np

from pyeda.inter import *

# Greek-only MS sort
def sortMsOps(mo1, mo2):
    mo1 = str(mo1)
    mo2 = str(mo2)
    ms1 = mo1[2:] if mo1[:1] == '~' else mo1[1:]
    ms2 = mo2[2:] if mo2[:1] == '~' else mo2[1:]

    c1 = ms1[:1]
    c2 = ms2[:1]
    if c1 == 'P' and c2 != 'P':
        return -1
    elif c1 != 'P' and c2 == 'P':
        return 1

    if c1 == '0' and c2 != '0':
        return -1
    elif c1 != '0' and c2 == '0':
        return 1

    # to get here, both MSS must be the same denomination!
    if c1 == 'P' or c1 == '0':
        ms1 = ms1[1:]
        ms2 = ms2[1:]

    if int(ms1) < int(ms2):
        return -1
    elif int(ms1) > int(ms2):
        return 1

    return 0 # same MS!

def cmp_to_key(sortMsOps):
    # Convert a cmp= function into a key= function
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return sortMsOps(self.obj, other.obj) < 0
        def __gt__(self, other):
            return sortMsOps(self.obj, other.obj) > 0
        def __eq__(self, other):
            return sortMsOps(self.obj, other.obj) == 0
        def __le__(self, other):
            return sortMsOps(self.obj, other.obj) <= 0  
        def __ge__(self, other):
            return sortMsOps(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return sortMsOps(self.obj, other.obj) != 0
    return K

class QCAAnalyzer:

    def __init__(s):
        s.df = None
        s.positive = None
        s.negative = None
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

    def generateExpressions(s, basename):
        # from collections import OrderedDict
        # OrderedDict(sorted(row[1:-1].to_dict().items()))
        s.mscols = ['M' + x for x in s.df.columns.values[1:-1]]
        pos_dbg = neg_dbg = ''
        for ridx in range(0, s.df.shape[0]):
            row = s.df.iloc[ridx]
            out = s.df.iloc[ridx]['OUT']
            label = s.df.iloc[ridx]['C1']
            msrow = row[1:-1]

            expression = None
            exp_dbg = label
            for cidx in range(0, len(s.mscols)):
                col = s.mscols[cidx]
                val = msrow[cidx]
                if val == '-':
                    continue

                exp = And(col) if str(val) == '1' else And(Not(col))
                exp_dbg = exp_dbg + ' ' + str(val) + col
                if expression:
                    expression = And(expression, exp)
                else:
                    expression = exp

            if out == 1:
                if s.positive:
                    s.positive = Or(s.positive, expression)
                    pos_dbg = pos_dbg + '\n' + exp_dbg
                else:
                    s.positive = Or(expression)
                    pos_dbg = exp_dbg
            elif out == 0:
                if s.negative:
                    s.negative = Or(s.negative, expression)
                    neg_dbg = neg_dbg + '\n' + exp_dbg
                else:
                    s.negative = Or(expression)
                    neg_dbg = exp_dbg

        dbgfile = s.config.get('csvBoolFolder') + basename + '-dbg-pos.txt'
        with open(dbgfile, 'w+') as dfile:
            dfile.write(pos_dbg)
            dfile.close
        dbgfile = s.config.get('csvBoolFolder') + basename + '-dbg-neg.txt'
        with open(dbgfile, 'w+') as dfile:
            dfile.write(neg_dbg)
            dfile.close


    def writeExpressions(s, basename):
        s.writeOutcomeExpr(basename, 'neg')
        s.writeOutcomeExpr(basename, 'pos')

    def writeOutcomeExpr(s, basename, outcome):
        c = s.config

        expressions = s.positive if outcome == 'pos' else s.negative
        expfile = c.get('csvBoolFolder') + basename + '-expr-' + outcome + '.txt'
        with open(expfile, 'w+') as efile:
            efile.write(str(expressions))
            efile.close

        minimized = espresso_exprs(expressions)
        minfile = c.get('csvBoolFolder') + basename + '-min-' + outcome + '.txt'
        with open(minfile, 'w+') as mfile:
            mfile.write(str(minimized))
            mfile.close

        sorted_terms = []
        trmfile = c.get('csvBoolFolder') + basename + '-' + outcome + '.txt'
        with open(trmfile, 'w+') as tfile:
            orset = minimized[0]._lits
            for andset in orset:
                msops = list(andset._lits)
                msops.sort(key=cmp_to_key(sortMsOps))
                sorted_terms.append(msops)
                for msop in msops:
                    tfile.write(str(msop) + '\t')
                tfile.write('\n')
            tfile.close

        csvfile = c.get('csvBoolFolder') + basename + '-' + outcome + '.csv'
        with open(csvfile, 'w+') as cfile:
            col_str = '\t'.join(s.mscols)
            cfile.write(col_str + '\n')
            for expr in sorted_terms:
                exp_str = ' '.join(str(x) for x in expr) + ' ' # to match last MS with suffixed space
                csv_line = ''
                for ms in s.mscols:
                    if ms + ' ' in exp_str:
                        if '~' + ms + ' ' in exp_str:
                            csv_line = csv_line + '0' + '\t'
                        else:
                            csv_line = csv_line + '1' + '\t'
                    else:
                        csv_line = csv_line + '-\t'
                cfile.write(csv_line + '\n')
            cfile.close

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
        s.generateExpressions(basename)
        s.writeExpressions(basename)

        s.info('Done')

# Invoke via entry point
# qcaAnalyzer.py -v -f [filename minus suffix]
# qcaAnalyzer.py -v -f test4
QCAAnalyzer().main(sys.argv[1:])
