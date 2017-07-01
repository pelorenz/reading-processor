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
        
        s.raw_exprs_P = None
        s.raw_exprs_N = None

        s.caseMapOnes = {}
        s.caseMapZeros = {}

        s.referenceMap = {}  # initial refs
        s.assignedCases = {} # refs assigned by algorithm
        s.manualCases = {}   # refs assigned manually

        s.minimized_exprs_P = []
        s.minimized_exprs_N = []

        s.all_exprs = []

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
            if row[:-1].count('0') != len(row) - 1 and row[:-1].count('1') != len(row) - 1 and row[:-1].count('-') != len(row) - 1:
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

        # TODO: fix me! references required to be contiguous
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
                vu_refs.append(s.refs[ridx])
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
            out = str(row[-1:][0])
            ref = s.refs[ridx]
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
                if s.raw_exprs_P:
                    s.raw_exprs_P = Or(s.raw_exprs_P, expression)
                else:
                    s.raw_exprs_P = Or(expression)

                if not d_key in s.caseMapOnes:
                    s.caseMapOnes[d_key] = []
                cases = s.caseMapOnes[d_key]
                cases.append(ref)
                s.caseMapOnes[d_key] = cases
                s.referenceMap[ref] = { 'expression': expression, 'dnfKey': d_key, 'outcome': '1'}
            elif out == '0':
                if s.raw_exprs_N:
                    s.raw_exprs_N = Or(s.raw_exprs_N, expression)
                else:
                    s.raw_exprs_N = Or(expression)

                if not d_key in s.caseMapZeros:
                    s.caseMapZeros[d_key] = []
                cases = s.caseMapZeros[d_key]
                cases.append(ref)
                s.caseMapZeros[d_key] = cases
                s.referenceMap[ref] =  { 'expression': expression, 'dnfKey': d_key, 'outcome': '0'}

    def minimizeExpressions(s):
        s.minimize('pos')
        s.minimize('neg')

        # manually add missing cases
        for ref in s.refs:
            if not ref in s.assignedCases:
                if ref in s.referenceMap:
                    ref_info = s.referenceMap[ref]

                    # already in manual list?
                    dnf_key = ref_info['dnfKey']
                    if dnf_key in s.manualCases:
                        expinf = s.manualCases[dnf_key]
                        expinf['cases'].append(ref)
                    else: # add new
                        msops = list(ref_info['expression']._lits)
                        expinf = {'msVars': msops, 'cases': [ref], 'dnfKey': dnf_key, 'source': 'manual'}

                        if ref_info['outcome'] == '1':
                            s.minimized_exprs_P.append(expinf)
                        elif ref_info['outcome'] == '0':
                            s.minimized_exprs_N.append(expinf)

                        s.manualCases[dnf_key] = expinf

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

    def lookupMissingKeys(s, msops, caseMap, min_key):
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

        # update with combined cases
        caseMap[min_key] = cases

        return cases

    def minimize(s, outcome):
        raw_exprs = s.raw_exprs_P if outcome == 'pos' else s.raw_exprs_N
        minimized_exprs = s.minimized_exprs_P if outcome == 'pos' else s.minimized_exprs_N
        caseMap = s.caseMapOnes if outcome == 'pos' else s.caseMapZeros

        # Perform Boolean minimization
        minimized = espresso_exprs(raw_exprs)

        orset = minimized[0]._lits
        for andset in orset:
            msops = list(andset._lits)
            msops.sort(key=cmp_to_key(sortMsOps))

            # TODO: fix me! depends on order of input CSV
            d_key = str(andset.to_dnf())
            cases = []
            if d_key in caseMap:
                cases = caseMap[d_key]
            else:
                cases = s.lookupMissingKeys(msops, caseMap, d_key)

            minimized_exprs.append({'msVars': msops, 'cases': cases, 'dnfKey': d_key, 'source': 'espresso'})

            # register cases assigned by espresso
            for case in cases:
                s.assignedCases[case] = (msops, d_key)

    def appendScores(s, expr, cases, dnf_key, incl, cov, outcome, out_id, source):
        scores = {}
        scores['expressions'] = expr
        scores['cases'] = cases
        scores['dnfKey'] = dnf_key
        scores['inclusion'] = incl
        scores['coverage'] = cov
        scores['outcome'] = outcome
        scores['outcomeID'] = out_id
        scores['source'] = source

        s.all_exprs.append(scores)

    def generateOutcomeID(s, prefix, id):
        oid = ''
        if id < 10:
            oid = prefix + '00' + str(id)
        elif id < 100:
            oid = prefix + '0' + str(id)
        else:
            oid = prefix + str(id)
        return oid

    def computeScores(s):
        # Total positive and negative cases for coverage
        p_outcomes = 0
        for expinfo in s.minimized_exprs_P:
            p_outcomes = p_outcomes + len(expinfo['cases'])

        n_outcomes = 0
        for expinfo in s.minimized_exprs_N:
            n_outcomes = n_outcomes + len(expinfo['cases'])

        # Iterate positive outcomes and compare to negative
        outcome_ctr = 1
        for expinf in s.minimized_exprs_P:
            expr = expinf['msVars']
            cases = expinf['cases']
            dnf_key = expinf['dnfKey']
            source = expinf['source']

            p_cases = len(cases)

            # Number of negative cases for current expression
            if dnf_key in s.caseMapZeros:
                n_cases = len(s.caseMapZeros[dnf_key])
            else:
                n_cases = 0

            inclusion = p_cases / (p_cases + n_cases) if n_cases > 0 else 1
            inclusion = '%.4f' % round(inclusion, 4) if inclusion != 1 else '1.0'

            coverage = p_cases / p_outcomes
            coverage = '%.4f' % round(coverage, 4)

            s.appendScores(expr, cases, dnf_key, inclusion, coverage, '1', s.generateOutcomeID('A', outcome_ctr), source)
            outcome_ctr = outcome_ctr + 1

        # Iterate negative outcomes and compare to positive
        outcome_ctr = 1
        for expinf in s.minimized_exprs_N:
            expr = expinf['msVars']
            cases = expinf['cases']
            dnf_key = expinf['dnfKey']
            source = expinf['source']

            n_cases = len(cases)

            # Number of positive cases for current expression
            if dnf_key in s.caseMapOnes:
                p_cases = len(s.caseMapOnes[dnf_key])
            else:
                p_cases = 0

            inclusion = n_cases / (p_cases + n_cases) if p_cases > 0 else 1
            inclusion = '%.4f' % round(inclusion, 4) if inclusion != 1 else '1.0'

            coverage = n_cases / n_outcomes
            coverage = '%.4f' % round(coverage, 4)

            s.appendScores(expr, cases, dnf_key, inclusion, coverage, '0', s.generateOutcomeID('B', outcome_ctr), source)
            outcome_ctr = outcome_ctr + 1

        return None

    def writeExpressions(s, basename):
        c = s.config

        csvfile = c.get('csvBoolFolder') + basename + '-results.csv'
        with open(csvfile, 'w+') as cfile:
            col_str = '\t'.join(s.mscols)
            cfile.write('ID\t' + col_str + '\tOutcome\tCases\tInclusion\tCoverage\tOnes\tDon\'t Cares\tSource\tReferences\tDNF\n')
            for res in s.all_exprs:
                ones = 0
                dontCares = 0

                exp_str = ' '.join(str(x) for x in res['expressions']) + ' ' # to match last MS with suffixed space
                csv_line = res['outcomeID'] + '\t'
                for ms in s.mscols:
                    if ms + ' ' in exp_str:
                        if '~' + ms + ' ' in exp_str:
                            csv_line = csv_line + '0' + '\t'
                        else:
                            csv_line = csv_line + '1' + '\t'
                            ones = ones + 1
                    else:
                        csv_line = csv_line + '-\t'
                        dontCares = dontCares + 1

                csv_line = csv_line + res['outcome'] + '\t'
                csv_line = csv_line + str(len(res['cases'])) + '\t'
                csv_line = csv_line + str(res['inclusion']) + '\t'
                csv_line = csv_line + str(res['coverage']) + '\t'
                csv_line = csv_line + str(ones) + '\t'
                csv_line = csv_line + str(dontCares) + '\t'
                csv_line = csv_line + res['source'] + '\t'
                csv_line = csv_line + '; '.join(res['cases']) + '\t'
                csv_line = csv_line + str(res['dnfKey'])
                cfile.write(csv_line + '\n')
            cfile.close

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        boolFile = None
        basename = ''
        if o.file:
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
        s.minimizeExpressions()
        s.computeScores()
        s.writeExpressions(basename)

        s.info('Done')

# Invoke via entry point
# qcaAnalyzer.py -v -f [filename minus suffix]
# qcaAnalyzer.py -v -f test4
QCAAnalyzer().main(sys.argv[1:])
