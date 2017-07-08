#! python3.6
# -*- coding: utf-8 -*-

import sys, os, string, re, errno

from object.util import *

from utility.config import *
from utility.options import *

from pyeda.inter import *

# Expressions sort
def sortExpressions(e1, e2):
    if e1['outcome'] == '1' and e2['outcome'] != '1':
        return -1
    elif e1['outcome'] != '1' and e2['outcome'] == '1':
        return 1

    if e1['ones'] < e2['ones']:
        return -1
    elif e1['ones'] > e2['ones']:
        return 1

    if len(e1['cases']) > len(e2['cases']):
        return -1
    elif len(e1['cases']) < len(e2['cases']):
        return 1

    return 0

def cmp_to_key_exprs(sortExpressions):
    # Convert a cmp= function into a key= function
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return sortExpressions(self.obj, other.obj) < 0
        def __gt__(self, other):
            return sortExpressions(self.obj, other.obj) > 0
        def __eq__(self, other):
            return sortExpressions(self.obj, other.obj) == 0
        def __le__(self, other):
            return sortExpressions(self.obj, other.obj) <= 0  
        def __ge__(self, other):
            return sortExpressions(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return sortExpressions(self.obj, other.obj) != 0
    return K

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

    if c1 == 'v' and c2 != 'v':
        return 1
    elif c1 != 'v' and c2 == 'v':
        return -1

    if c1 == 'V' and c2 != 'V':
        return 1
    elif c1 != 'V' and c2 == 'V':
        return -1

    # to get here, both MSS must be the same denomination!
    if c1 == 'P' or c1 == '0':
        ms1 = ms1[1:]
        ms2 = ms2[1:]
    elif c1 == 'V':
        ms1 = ms1[2:]
        ms2 = ms2[2:]
    else: # vg, should not get here
        ms1 = '1000'
        ms2 = '1001'

    if int(ms1) < int(ms2):
        return -1
    elif int(ms1) > int(ms2):
        return 1

    return 0 # same MS!

def cmp_to_key_msops(sortMsOps):
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

def sortDC(ex1, ex2):
    if len(ex1['msVars']) > len(ex2['msVars']):
        return -1
    elif len(ex1['msVars']) < len(ex2['msVars']):
        return 1
    else:
        return 0

def cmp_to_key_dc(sortDC):
    # Convert a cmp= function into a key= function
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return sortDC(self.obj, other.obj) < 0
        def __gt__(self, other):
            return sortDC(self.obj, other.obj) > 0
        def __eq__(self, other):
            return sortDC(self.obj, other.obj) == 0
        def __le__(self, other):
            return sortDC(self.obj, other.obj) <= 0  
        def __ge__(self, other):
            return sortDC(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return sortDC(self.obj, other.obj) != 0
    return K

class QCAAnalyzer:

    def __init__(s):
        s.csv = []
        s.mscols = []
        s.refs = []
        s.metaData = []

        s.raw_exprs_P = None
        s.raw_exprs_N = None

        s.caseMapOnes = {}
        s.caseMapZeros = {}

        s.referenceMap = {}  # initial refs
        s.assignedCases = {} # refs assigned by algorithm
        s.manualCases = {}   # refs assigned manually

        s.caseOutcomes = {}

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
        with open(filename, 'r', encoding='utf-8') as file:
            s.info('reading', filename)
            csvdata = file.read()
            file.close()

        rows = csvdata.split('\n')
        for idx, row in enumerate(rows):
            parts = row.split('\t')
            if len(parts) == 1:
                continue
            if idx == 0: # colnames
                for m in parts[5:]:
                    if m == 'OUT':
                        continue

                    if re.match(r'^[\d]', m):
                        s.mscols.append('M' + m)
                    elif re.match(r'^[A-Za-z]', m):
                        s.mscols.append(m)
                continue

            s.refs.append(parts[:1][0])
            s.metaData.append({'aggregateData': parts[1:2][0], 'witnessStr': parts[3:4][0], 'excerpt': parts[4:5][0]})
            s.csv.append(parts[5:])

    def filterRow(s, new_refs, new_metaData, new_csv, vu_refs, vu_csv, vu_mdata):
        # All-zero/one rows?
        csv = []
        refs = []
        m_data = []
        for ridx, row in enumerate(vu_csv):
            if row[:-1].count('0') + row[:-1].count('-') != len(row) - 1 and row[:-1].count('1') != len(row) - 1 and row[:-1].count('-') != len(row) - 1:
                csv.append(row)
                refs.append(vu_refs[ridx])
                m_data.append(vu_mdata[ridx])

        if len(csv) <= 1:
            return

        new_csv.extend(csv)
        new_refs.extend(refs)
        new_metaData.extend(m_data)

    def prepareCSV(s):
        new_csv = []
        vu_csv = []
        new_refs = []
        vu_refs = []
        new_metaData = []
        vu_mdata = []

        # TODO: fix me! references required to be contiguous
        cur_ref = ''
        for ridx, ref in enumerate(s.refs):
            vuref = re.sub(r'[a-z]$', '', ref)
            if vuref != cur_ref:
                cur_ref = vuref
                s.filterRow(new_refs, new_metaData, new_csv, vu_refs, vu_csv, vu_mdata)
                vu_csv = []
                vu_refs = []
                vu_mdata = []
            elif ridx == len(s.refs) - 1: # last time
                vu_csv.append(s.csv[ridx])
                vu_refs.append(s.refs[ridx])
                vu_mdata.append(s.metaData[ridx])
                s.filterRow(new_refs, new_metaData, new_csv, vu_refs, vu_csv, vu_mdata)
                break # Done!

            vu_csv.append(s.csv[ridx])
            vu_refs.append(s.refs[ridx])
            vu_mdata.append(s.metaData[ridx])

        s.csv = new_csv
        s.refs = new_refs
        s.metaData = new_metaData

    def writeCSV(s, basename):
        c = s.config

        csvfile = c.get('csvBoolFolder') + basename + '-revised.csv'
        with open(csvfile, 'w+', encoding='utf-8') as cfile:
            cfile.write('C1\t' + '\t'.join(s.mscols) + '\n')
            for idx, row in enumerate(s.csv):
                cfile.write(s.refs[idx] + '\t' + '\t'.join(row) + '\n')
            cfile.close()

    def generateExpressions(s, basename):
        for ridx, row in enumerate(s.csv):
            out = str(row[-1:][0])
            ref = s.refs[ridx]
            m_data = s.metaData[ridx]
            msrow = row[:-1]

            expression = None
            attestingMSS = []
            for cidx, col in enumerate(s.mscols):
                val = msrow[cidx]
                if val == '-':
                    continue

                if str(val) == '1':
                    exp = And(col)
                    attestingMSS.append(col)
                else:
                    exp = And(Not(col))

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
                s.referenceMap[ref] = { 'expression': expression, 'dnfKey': d_key, 'attestingMSS': attestingMSS, 'outcome': '1', 'aggregateData': m_data['aggregateData'], 'witnessStr': m_data['witnessStr'], 'excerpt': m_data['excerpt'] }
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
                s.referenceMap[ref] =  { 'expression': expression, 'dnfKey': d_key, 'attestingMSS': attestingMSS, 'outcome': '0', 'aggregateData': m_data['aggregateData'], 'witnessStr': m_data['witnessStr'], 'excerpt': m_data['excerpt'] }

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
                        vars = list(ref_info['expression']._lits)
                        expinf = {'msVars': vars, 'cases': [ref], 'dnfKey': dnf_key, 'source': 'manual'}

                        if ref_info['outcome'] == '1':
                            s.minimized_exprs_P.append(expinf)
                        elif ref_info['outcome'] == '0':
                            s.minimized_exprs_N.append(expinf)

                        s.manualCases[dnf_key] = expinf

        # merge expressions that differ only in 0's and dc's
        s.minimized_exprs_P = s.mergeDCExpressions(s.minimized_exprs_P)
        s.minimized_exprs_N = s.mergeDCExpressions(s.minimized_exprs_N)

        # detect and merge expressions with mutual dc to 1, 1 to dc loops
        s.minimized_exprs_P = s.detectMatches(s.minimized_exprs_P)
        s.minimized_exprs_N = s.detectMatches(s.minimized_exprs_N)

    def buildExpressionsFromCases(s, expinf):
        build_parts = []
        for case in expinf['cases']:
            ref_info = s.referenceMap[case]
            if not build_parts:
                build_vars = list(ref_info['expression']._lits)
                build_str = ' '.join(str(x) for x in build_vars)
                build_parts = build_str.split(' ')
            else: # combine
                case_vars = list(ref_info['expression']._lits)
                case_str = ' '.join(str(x) for x in case_vars) + ' '
                case_parts = case_str.split(' ')

                work_parts = []
                for ms in s.mscols:
                    if ms in case_parts and ms in build_parts:
                        work_parts.append(ms)

                    if '~' + ms in case_parts and '~' + ms in build_parts:
                        work_parts.append('~' + ms)

                build_parts = work_parts

        vars = []
        for part in build_parts:
            if part[:1] == '~':
                vars.append(Not(part[1:]))
            else:
                vars.append(exprvar(part))

        expinf['msVars'] = vars

        # build expression
        expression = None
        for var in vars:
            if not expression:
                expression = var
            else:
                expression = And(expression, var)
        try:
            expinf['dnfKey'] = str(expression.to_dnf())
        except AttributeError as e:
            raise

    def isMatch(s, baseEx, testEx):
        if not baseEx['cases'] or not testEx['cases']:
            return False

        base_str = ' '.join(str(x) for x in baseEx['msVars']) + ' '
        test_str = ' '.join(str(x) for x in testEx['msVars']) + ' '
        for ms in s.mscols:
            base_val = ''
            if ms + ' ' in base_str:
                if '~' + ms + ' ' in base_str: # 0
                    base_val = '0'
                else: # 1
                    base_val = '1'
            else: # dc
                base_val = '-'

            test_val = ''
            if ms + ' ' in test_str:
                if '~' + ms + ' ' in test_str: # 0
                    test_val = '0'
                else: # 1
                    test_val = '1'
            else: # dc
                test_val = '-'

            if base_val == '1' and test_val == '0':
                return False
            elif base_val == '0' and test_val == '1':
                return False

        return True

    def findMatches(s, expinf, exprs):
        matches = []
        for ei in exprs:
            if s.isMatch(expinf, ei):
                if not matches:
                    matches.append(expinf)
                matches.append(ei)
        return matches

    def selectBaseMatch(s, exprs):
        base = None

        # find with most 1's
        max_ones = 0
        for ex in exprs:
            var_count = len(ex['msVars'])
            var_str = ' '.join(str(x) for x in ex['msVars'])
            tilde_count = var_str.count('~')
            ones = var_count - tilde_count

            if ones > max_ones:
                max_ones = ones
                base = ex

        base_str = ' '.join(str(x) for x in base['msVars'])
        base_parts = base_str.split(' ')
        base_parts = [ex for ex in base_parts if ex[:1] != '~']

        sub_list = [ex for ex in exprs if ex is not base]
        for ex in sub_list:
            ex_str = ' '.join(str(x) for x in ex['msVars'])
            ex_parts = ex_str.split(' ')
            ex_parts = [ex for ex in ex_parts if ex[:1] != '~']

            if not set(ex_parts).issubset(set(base_parts)):
                base = None # base does not represent all member vars!
                break

        return base

    def computeProfile(s, exprs):
        profile = set()
        for ex in exprs:
            ex_str = ' '.join(str(x) for x in ex['msVars'])
            ex_parts = ex_str.split(' ')
            ex_parts = [ex for ex in ex_parts if ex[:1] != '~']

            profile = profile.union(ex_parts)

        return profile

    def isMatchProfile(s, vars, profile):
        var_str = ' '.join(str(x) for x in vars)
        var_parts = var_str.split(' ')
        var_parts = [ex for ex in var_parts if ex[:1] != '~']

        if profile.issubset(set(var_parts)):
            return True

        return False

    def moveMatches(s, expinf, base, profile):
        keep_cases = []
        for case in expinf['cases']:
            ref_info = s.referenceMap[case]
            c_ex = ref_info['expression']

            if s.isMatchProfile(list(c_ex._lits), profile):
                if not case in base['cases']:
                    base['cases'].append(case)
            else:
                keep_cases.append(case)

        return keep_cases

    def combineMatches(s, exprs):
        base = s.selectBaseMatch(exprs)
        if not base:
            base = {'msVars': [], 'cases': [], 'dnfKey': '', 'source': 'postprocess'}

        sub_list = [ex for ex in exprs if ex is not base]
        profile = s.computeProfile(exprs)
        for ex in sub_list:
            case_count = len(ex['cases'])
            ex['cases'] = s.moveMatches(ex, base, profile)
            if ex['cases'] and len(ex['cases']) < case_count:
                s.buildExpressionsFromCases(ex)

        if base['cases']:
            s.buildExpressionsFromCases(base)
            sub_list.append(base)

        return sub_list

    def detectMatches(s, exprs):
        exprs_list = []
        for expinf in exprs:
            exprs_list.append(expinf)

        # sort from fewer to more dc's
        exprs_list.sort(key=cmp_to_key_dc(sortDC))

        # First pass
        match_groups = []
        for expinf in exprs_list:
            group = s.findMatches(expinf, [ex for ex in exprs_list if ex is not expinf])
            match_groups.append(group)

        for group in match_groups:
            g_survivors = [ex for ex in group if ex in exprs_list]
            if len(g_survivors) > 1:
                for ex in g_survivors:
                    if ex in exprs_list:
                        exprs_list.remove(ex)

                match_results = s.combineMatches(g_survivors)
                exprs_list.extend(match_results)

        # sort from fewer to more dc's - again
        exprs_list.sort(key=cmp_to_key_dc(sortDC))

        # Second pass
        match_groups = []
        for expinf in exprs_list:
            group = s.findMatches(expinf, [ex for ex in exprs_list if ex is not expinf])
            match_groups.append(group)

        for group in match_groups:
            g_survivors = [ex for ex in group if ex in exprs_list]
            if len(g_survivors) > 1:
                for ex in g_survivors:
                    if ex in exprs_list:
                        exprs_list.remove(ex)

                match_results = s.combineMatches(g_survivors)
                exprs_list.extend(match_results)

        return exprs_list

    def mergeDCExpressions(s, exprs):
        exprs_list = []

        infoMap = {}
        onesMap = {}
        dcMap = {}

        # merge expressions that differ only in 0's and dc's
        for expinf in exprs:
            key = ''
            ones_mss = []
            dc_mss = []
            var_str = ' '.join(str(x) for x in expinf['msVars']) + ' '
            for ms in s.mscols:
                # treat 0's and dc's the same for purpose of key
                if ms + ' ' in var_str:
                    if '~' + ms + ' ' in var_str: # 0
                        key = key + '0'
                    else: # 1
                        key = key + '1'
                        ones_mss.append(ms)
                else: # dc
                    key = key + '0'
                    dc_mss.append(ms)

            inf_list = []
            if key in infoMap:
                inf_list = infoMap[key]
            inf_list.append(expinf)
            infoMap[key] = inf_list

            dc_list = []
            if key in dcMap:
                dc_list = dcMap[key]
            dc_list.extend(dc_mss)
            dcMap[key] = dc_list

            # replacing each time ok bc ones in same position in key
            onesMap[key] = ones_mss

        # now merge the info objects
        for key, inf_list in infoMap.items():
            m_cases = []
            m_source = 'manual'
            m_vars = []
            expr = None
            for ms in s.mscols:
                var = None
                if ms in onesMap[key]: # 1
                    var = exprvar(ms)
                elif not ms in dcMap[key]: # 0
                    var = Not(ms)

                if var:
                    m_vars.append(var)
                    expr = And(expr, var) if expr else var

            dnf_key = str(expr.to_dnf())
            for inf in inf_list:
                for case in inf['cases']:
                    if not case in m_cases:
                        m_cases.append(case)
                
                if inf['source'] == 'espresso':
                    m_source = 'espresso'

            exprs_list.append({'msVars': m_vars, 'cases': m_cases, 'dnfKey': dnf_key, 'source': m_source})

        return exprs_list

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

    def deepCopyExpression(s, exp):
        exp2 = None
        if 'AndOp' in str(type(exp)) or 'Complement' in str(type(exp)):
            exps = list(exp._lits)
            exps.sort(key=cmp_to_key_msops(sortMsOps))
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

        return exp2

    def insertOp(s, reconstr, col):
        if len(reconstr) == 0:
            reconstr.append(And(col))
            reconstr.append(And(Not(col)))
            return reconstr
        else:
            new_rcstr = []

            # exp is a combination of preceding columns
            for exp in reconstr:
                # for cases where the missing column is attested 
                # and either supports or opposes the pattern,
                # generate two patterns, one supporting and the other
                # opposing

                # deep copy exp to exp2
                exp2 = s.deepCopyExpression(exp)

                # for cases where the missing column is not attested,
                # generate a third pattern lacking the column
                exp3 = s.deepCopyExpression(exp)

                exp = And(exp, col)
                exp2 = And(exp2, Not(col))
                new_rcstr.append(exp)
                new_rcstr.append(exp2)
                new_rcstr.append(exp3)
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
            else: # missing key - actually an important element of the path
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
            vars = list(andset._lits)
            vars.sort(key=cmp_to_key_msops(sortMsOps))

            # TODO: fix me! depends on order of input CSV
            d_key = str(andset.to_dnf())
            cases = []
            if d_key in caseMap:
                cases = caseMap[d_key]
            else:
                cases = s.lookupMissingKeys(vars, caseMap, d_key)

            minimized_exprs.append({'msVars': vars, 'cases': cases, 'dnfKey': d_key, 'source': 'espresso'})

            # register cases assigned by espresso
            for case in cases:
                s.assignedCases[case] = (vars, d_key)

    def appendScores(s, msVars, cases, dnf_key, incl, cov, outcome, out_id, source):
        scores = {}
        scores['msVars'] = msVars
        scores['cases'] = cases
        scores['dnfKey'] = dnf_key
        scores['inclusion'] = incl
        scores['coverage'] = cov
        scores['outcome'] = outcome
        scores['outcomeID'] = out_id
        scores['source'] = source

        # Compute number of 1's, for sorting
        ones = 0
        var_str = ' '.join(str(x) for x in msVars) + ' '
        for ms in s.mscols:
            if ms + ' ' in var_str and not '~' + ms + ' ' in var_str:
                ones = ones + 1
        scores['ones'] = ones

        s.all_exprs.append(scores)

    def generateOutcomeID(s, prefix, id):
        oid = ''
        if id < 10:
            oid = prefix + '0' + str(id)
        else:
            oid = prefix + str(id)
        return oid

    def assignCases(s, out_id, cases):
        for ref in cases:
            outcomes = []
            if ref in s.caseOutcomes:
                outcomes = s.caseOutcomes[ref]
            outcomes.append(out_id)
            s.caseOutcomes[ref] = outcomes

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
            msVars = expinf['msVars']
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

            out_id = s.generateOutcomeID('A', outcome_ctr)
            s.assignCases(out_id, cases)

            s.appendScores(msVars, cases, dnf_key, inclusion, coverage, '1', out_id, source)
            outcome_ctr = outcome_ctr + 1

        # Iterate negative outcomes and compare to positive
        outcome_ctr = 1
        for expinf in s.minimized_exprs_N:
            msVars = expinf['msVars']
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

            out_id = s.generateOutcomeID('B', outcome_ctr)
            s.assignCases(out_id, cases)

            s.appendScores(msVars, cases, dnf_key, inclusion, coverage, '0', out_id, source)
            outcome_ctr = outcome_ctr + 1

        s.all_exprs.sort(key=cmp_to_key_exprs(sortExpressions))

    def buildCaseStr(s, out_id, cases, isHTML):
        mssToCases = {}
        msKeys = []
        for case in cases:
            if case in s.referenceMap:
                ref_info = s.referenceMap[case]
                a_mss = ref_info['attestingMSS']
                a_mss = [m[1:] if m[:1] == 'M' else m for m in a_mss]
                ms_key = '+'.join(a_mss)

                c_list = []
                if ms_key in mssToCases:
                    c_list = mssToCases[ms_key]
                else:
                    msKeys.append(ms_key)
                c_list.append(case)
                mssToCases[ms_key] = c_list

        casestr = ''
        for key in msKeys:
            if isHTML:
                casestr = casestr + '<span class="expr">[' + key + ']</span> '
            else:
                casestr = casestr + '[' + key + '] '

            cases = mssToCases[key]
            for ref in cases:
                o_str = ''
                outcomes = []
                if ref in s.caseOutcomes:
                    outcomes = s.caseOutcomes[ref]
                    if len(outcomes) > 1:
                        o_str = ' ('
                        for oc in outcomes:
                            if oc == out_id:
                                continue
                            if o_str[-1:] != '(':
                                o_str = o_str + ', '
                            o_str = o_str + oc
                        o_str = o_str + ')'

                casestr = casestr + ref + o_str + '; '

        return casestr[:-2] # subtract final semicolon and space

    def buildDetails(s, cases):
        mssToCases = {}
        msKeys = []
        for case in cases:
            if case in s.referenceMap:
                ref_info = s.referenceMap[case]
                a_mss = ref_info['attestingMSS']
                a_mss = [m[1:] if m[:1] == 'M' else m for m in a_mss]
                ms_key = '+'.join(a_mss)

                c_list = []
                if ms_key in mssToCases:
                    c_list = mssToCases[ms_key]
                else:
                    msKeys.append(ms_key)
                c_list.append(case)
                mssToCases[ms_key] = c_list

        details = '<div>.</div>'
        for key in msKeys:
            #details = details + '<div>[' + key + ']</div>'

            cases = mssToCases[key]
            for ref in cases:
                ref_info = s.referenceMap[ref]
                details = details + '<div><b>' + ref + '</b> ' + ref_info['witnessStr'] + ': ' + ref_info['excerpt'] + '</div>'
                if ref_info['aggregateData']:
                    details = details + '<div>' + ref_info['aggregateData'] + '</div>'
                details = details + '<div>.</div>'

        return details[:-2] # subtract final returns

    def writeExpressions(s, basename):
        c = s.config

        subdir = re.sub(r'^c', '', basename)
        subdir = re.sub(r'[DLMgl]{1,3}$', '', subdir)
        subdir = 'Mark ' + subdir + 'QCA'
        htmldir = c.get('statsFolder') + subdir + '/'
        try:
            os.makedirs(htmldir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        htmlfile = htmldir + basename + '-header.html'
        cols = [m[1:] if m[:1] == 'M' else m for m in s.mscols]
        with open(htmlfile, 'w+', encoding='utf-8') as hfile:
            col_str = '</td><td class="ms">'.join(cols)
            hfile.write('<table cellspacing="0" cellpadding="0" id="qca-hdr"><tr class="qca"><td class="id">ID</td><td class="ms">' + col_str + '</td><td class="ms">Out</td><td class="small">Cs</td><td class="small">1s</td><td class="small">DC</td><td class="medium">Inc</td><td class="medium">Cov</td><td class="small">Sc</td><td class="ref-head">References</td></tr></table>')

            hfile.close()

        htmlfile = htmldir + basename + '.html'
        with open(htmlfile, 'w+', encoding='utf-8') as hfile:
            hfile.write('<div id="qca-div"><table cellspacing="0" cellpadding="0" id="qca-table">\n')

            for res in s.all_exprs:
                dontCares = 0

                var_str = ' '.join(str(x) for x in res['msVars']) + ' ' # to match last MS with suffixed space

                hfile.write('<tr class="qca"><td class="id">' + res['outcomeID'] + '</td>')
                for ms in s.mscols:
                    m_disp = ms[1:] if ms[:1] == 'M' else ms
                    hilite = 'X' + m_disp if m_disp[:1].isdigit() else m_disp
                    if ms + ' ' in var_str:
                        if '~' + ms + ' ' in var_str:
                            hfile.write('<td class="ms">' + '0' + '</td>')
                        else:
                            hfile.write('<td class="ms ' + hilite + '">' + '1' + '</td>')
                    else:
                        hfile.write('<td class="ms dontcare">' + '-' + '</td>')
                        dontCares = dontCares + 1

                hfile.write('<td class="ms">' + res['outcome'] + '</td>')
                hfile.write('<td class="small cases">' + str(len(res['cases'])) + '</td>')
                hfile.write('<td class="small ones">' + str(res['ones']) + '</td>')
                hfile.write('<td class="small">' + str(dontCares) + '</td>')
                hfile.write('<td class="medium">' + str(res['inclusion']) + '</td>')
                hfile.write('<td class="medium">' + str(res['coverage']) + '</td>')

                src = res['source'][:1].upper()
                hfile.write('<td class="small">' + src + '</td>')

                case_str = s.buildCaseStr(res['outcomeID'], res['cases'], True)
                details = s.buildDetails(res['cases'])
                hfile.write('<td class="ref" onclick="DSS.refClick(event)">' + case_str + '<div class="ref-body ref-hidden">' + details + '</div></td></tr>')

            hfile.write('</table>')
            hfile.write('<div>.</div>')
            hfile.write('<div>Chapter: ' + re.sub(r'\-[0-9VLvgP]{1,4}[LDMgl]{1,3}$', '', basename) + '</div>')
            witness = re.sub(r'^c\d{2,2}\-', '', basename)
            witness = re.sub(r'[LDMgl]{1,3}$', '', witness)
            hfile.write('<div>Reference witness: ' + witness + '</div>')

            vars = {}
            for ref in s.refs:
                ref = re.sub(r'[a-z]$', '', ref)
                vars[ref] = None
            hfile.write('<div>Variation units: ' + str(len(vars)) + '</div>')
            hfile.write('<div>Readings: ' + str(len(s.csv)) + '</div>')
            hfile.write('<div>Expressions: ' + str(len(s.all_exprs)) + '</div>')
            hfile.write('<div>Positive outcomes: ' + str(len(s.minimized_exprs_P)) + '</div>')
            hfile.write('<div>Negative outcomes: ' + str(len(s.minimized_exprs_N)) + '</div>')
            hfile.write('</div>')
            hfile.close

        csvfile = c.get('csvBoolFolder') + basename + '-results.csv'
        with open(csvfile, 'w+', encoding='utf-8') as cfile:
            col_str = '\t'.join(s.mscols)
            cfile.write('ID\t' + col_str + '\tOutcome\tCases\tInclusion\tCoverage\tOnes\tDon\'t Cares\tSource\tReferences\tDNF\n')

            for res in s.all_exprs:
                dontCares = 0

                var_str = ' '.join(str(x) for x in res['msVars']) + ' ' # to match last MS with suffixed space
                csv_line = res['outcomeID'] + '\t'
                for ms in s.mscols:
                    if ms + ' ' in var_str:
                        if '~' + ms + ' ' in var_str:
                            csv_line = csv_line + '0' + '\t'
                        else:
                            csv_line = csv_line + '1' + '\t'
                    else:
                        csv_line = csv_line + '-\t'
                        dontCares = dontCares + 1

                csv_line = csv_line + res['outcome'] + '\t'
                csv_line = csv_line + str(len(res['cases'])) + '\t'
                csv_line = csv_line + str(res['inclusion']) + '\t'
                csv_line = csv_line + str(res['coverage']) + '\t'
                csv_line = csv_line + str(res['ones']) + '\t'
                csv_line = csv_line + str(dontCares) + '\t'

                csv_line = csv_line + res['source'] + '\t'

                case_str = s.buildCaseStr(res['outcomeID'], res['cases'], False)
                csv_line = csv_line + case_str + '\t'
                csv_line = csv_line + str(res['dnfKey'])

                cfile.write(csv_line + '\n')
             
            cfile.close

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        basename = ''
        if o.file:
            basename = o.file
        else:
            basename = c.get('qcaBaseFileName')

        if not basename:
            return

        qcaPaths = []
        qcaPaths.append(c.get('csvBoolFolder') + basename + 'D.csv')
        qcaPaths.append(c.get('csvBoolFolder') + basename + 'L.csv')
        qcaPaths.append(c.get('csvBoolFolder') + basename + 'Dgl.csv')
        qcaPaths.append(c.get('csvBoolFolder') + basename + 'M.csv')

        for path in qcaPaths:
            basename = path[len(c.get('csvBoolFolder')):-4]

            s.__init__()
            s.loadCSV(path)
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
