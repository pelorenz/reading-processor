#! python3.6
# -*- coding: utf-8 -*-

import sys, os, string, re

from object.util import *

from utility.config import *
from utility.options import *

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
        s.csv = []
        s.mscols = []
        s.refs = []
        
        s.positive = None
        s.negative = None

        s.caseMapOnes = {}
        s.caseMapZeros = {}

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

        csvdata = ''
        with open(filename, 'r') as file:
            s.info('reading', filename)
            csvdata = file.read()
            file.close()

        rows = csvdata.split('\n')
        for idx, row in enumerate(rows):
            parts = row.split('\t')
            if idx == 0: # colnames
                s.mscols = ['M' + c for c in parts[1:] if re.match(r'^[\dP]', c)]
                continue

            s.refs.append(parts[:1][0])
            s.csv.append(parts[1:])

    def filterRow(s, new_refs, new_csv, vu_refs, vu_csv):
        # All-zero/one rows?
        csv = []
        refs = []
        for ridx, row in enumerate(vu_csv):
            if row.count('0') + row.count('-') != len(row) and row.count('1') + row.count('-') != len(row):
                csv.append(row)
                refs.append(vu_refs[ridx])

        if len(csv) == 0:
            return

        new_csv.extend(csv)
        new_refs.extend(refs)

    def prepareCSV(s):
        new_csv = []
        vu_csv = []
        new_refs = []
        vu_refs = []

        cur_ref = ''
        for ridx, ref in enumerate(s.refs):
            vuref = re.sub(r'[a-z]$', '', ref)
            if vuref != cur_ref:
                cur_ref = vuref
                s.filterRow(new_refs, new_csv, vu_refs, vu_csv)
                vu_csv = []
                vu_refs = []
            elif ridx == len(s.refs) - 1: # last time
                vu_csv.append(s.csv[ridx])
                vu_refs.append(s.refs[rid])
                s.filterRow(new_refs, new_csv, vu_refs, vu_csv)
                break # Done!

            vu_csv.append(s.csv[ridx])
            vu_refs.append(s.refs[ridx])

        s.csv = new_csv
        s.refs = new_refs

    def writeCSV(s, basename):
        c = s.config

        csvfile = c.get('csvBoolFolder') + basename + '-revised.csv'
        with open(csvfile, 'w+') as cfile:
            cfile.write('C1\t' + '\t'.join(s.mscols) + '\n')
            for idx, row in enumerate(s.csv):
                cfile.write(s.refs[idx] + '\t' + '\t'.join(row) + '\n')
            cfile.close()

    def generateExpressions(s, basename):
        for ridx, row in enumerate(s.csv):
            out = row[-1:][0]
            label = s.refs[ridx]
            msrow = row[:-1]

            expression = None
            for cidx, col in enumerate(s.mscols):
                val = msrow[cidx]
                if val == '-':
                    continue

                exp = And(col) if str(val) == '1' else And(Not(col))
                if expression:
                    expression = And(expression, exp)
                else:
                    expression = exp

            d_key = str(expression.to_dnf())
            if out == '1':
                if s.positive:
                    s.positive = Or(s.positive, expression)
                else:
                    s.positive = Or(expression)

                if not d_key in s.caseMapOnes:
                    s.caseMapOnes[d_key] = []
                cases = s.caseMapOnes[d_key]
                cases.append(label)
                s.caseMapOnes[d_key] = cases
            elif out == '0':
                if s.negative:
                    s.negative = Or(s.negative, expression)
                else:
                    s.negative = Or(expression)

                if not d_key in s.caseMapZeros:
                    s.caseMapZeros[d_key] = []
                cases = s.caseMapZeros[d_key]
                cases.append(label)
                s.caseMapZeros[d_key] = cases

    def writeExpressions(s, basename):
        s.writeOutcomeExpr(basename, 'neg')
        s.writeOutcomeExpr(basename, 'pos')

    def passOp(s, reconstr, col, slice):
        if len(reconstr) == 0:
            exp = And(col) if slice == 'pos' else And(Not(col))
            reconstr.append(exp)
            return reconstr
        else:
            new_rcstr = []
            for exp in reconstr:
                exp = And(exp, col) if slice == 'pos' else And(exp, Not(col))
                new_rcstr.append(exp)
            return new_rcstr

    def insertOp(s, reconstr, col):
        if len(reconstr) == 0:
            reconstr.append(And(col))
            reconstr.append(And(Not(col)))
            return reconstr
        else:
            new_rcstr = []
            for exp in reconstr:
                # deep copy exp to exp2
                exp2 = None
                if 'AndOp' in str(type(exp)) or 'Complement' in str(type(exp)):
                    exps = list(exp._lits)
                    exps.sort(key=cmp_to_key(sortMsOps))
                    for e in exps:
                        e = str(e)
                        ms = e[1:] if '~' == e[:1] else e
                        if not exp2:
                            exp2 = And(Not(ms)) if '~' == e[:1] else And(ms)
                        else:
                            exp2 = And(exp2, Not(ms)) if '~' == e[:1] else And(exp2, ms)
                elif 'Variable' in str(type(exp)):
                    exp2 = exprvar(exp.names[0])
                else:
                    raise ValueError('Unexpected type ' + str(type(exp)))

                exp = And(exp, col)
                exp2 = And(exp2, Not(col))
                new_rcstr.append(exp)
                new_rcstr.append(exp2)
            return new_rcstr

    def lookupMissingKeys(s, msops, caseMap):
        cases = []
        reconstr_ops = [] # list of And expressions

        # Search for missing keys and insert plus/minus values
        for col in s.mscols:
            if exprvar(col) in msops:
                reconstr_ops = s.passOp(reconstr_ops, col, 'pos')
            elif Not(col) in msops:
                reconstr_ops = s.passOp(reconstr_ops, col, 'neg')
            else: # missing key!
                reconstr_ops = s.insertOp(reconstr_ops, col)

        # Assemble cases
        for exp in reconstr_ops:
            d_key = str(exp.to_dnf())
            if d_key in caseMap:
                cases.extend(caseMap[d_key])

        return cases

    def writeOutcomeExpr(s, basename, outcome):
        c = s.config

        expressions = s.positive if outcome == 'pos' else s.negative
        caseMap = s.caseMapOnes if outcome == 'pos' else s.caseMapZeros
        minimized = espresso_exprs(expressions)

        sorted_terms = []
        orset = minimized[0]._lits
        for andset in orset:
            msops = list(andset._lits)
            msops.sort(key=cmp_to_key(sortMsOps))

            d_key = str(andset.to_dnf())
            cases = []
            if d_key in caseMap:
                cases = caseMap[d_key]
                #s.info('key found:', d_key)
            else:
                #s.info('key not found:', d_key)
                cases = s.lookupMissingKeys(msops, caseMap)
            
            sorted_terms.append((msops, cases))

        csvfile = c.get('csvBoolFolder') + basename + '-' + outcome + '.csv'
        with open(csvfile, 'w+') as cfile:
            col_str = '\t'.join(s.mscols)
            cfile.write(col_str + '\tCases\tReferences\n')
            for (expr, cases) in sorted_terms:
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

                csv_line = csv_line + str(len(cases))
                csv_line = csv_line + '\t' + '; '.join(cases)
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
        s.prepareCSV()
        s.writeCSV(basename)
        s.generateExpressions(basename)
        s.writeExpressions(basename)

        s.info('Done')

# Invoke via entry point
# qcaAnalyzer.py -v -f [filename minus suffix]
# qcaAnalyzer.py -v -f test4
QCAAnalyzer().main(sys.argv[1:])
