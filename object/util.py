import sys, os, re

class Util:
    MS_OVERLAYS = [ 'na28' ]

    CORRECTOR_MSS = ['01', '05']

    BEZAE_HANDS = ['05*','sm','A','B','C','D','E','H','A/B']
    SINAI_HANDS = ['01*','A','C1','C2']

    CORE_GROUPS = ['F03', 'C565', 'F1', 'F13', 'CP45']

    group_map = {}
    g_prefixes = ['B', 'C', 'F', 'I', 'S']

def getGroupBase(group):
    s_res = re.search(r'^(Iso|[ByzCFP0-9]+)([s]{0,1})$', group)
    if s_res:
        group = s_res.group(1)
    return group

def makePart(tok, lpart):
    part = {}
    vtoks = tok.split('.') if '.' in tok else [ tok ]
    if len(vtoks) == 1:
        if not lpart:
            raise ValueError('Variant label requires initial verse identifier.')

        part['verse'] = lpart['verse']
        part['addresses'] = vtoks[0].split('-') if '-' in vtoks[0] else [ vtoks[0] ]
    elif len(vtoks) == 2:
        part['verse'] = vtoks[0]
        part['addresses'] = vtoks[1].split('-') if '-' in vtoks[1] else [ vtoks[1] ]
    else:
        raise ValueError('Malformed variant label.')
    return part

def makeParts(v):
    parts = []
    toks = v.split(',') if ',' in v else [ v ]
    lastpart = None
    for idx, tok in enumerate(toks):
        lastpart = makePart(tok, lastpart)
        parts.append(lastpart)
    return parts

def isDistinctive(groupAssignments, refMS, vu, reading, group):
    if not reading or vu.isReferenceSingular(refMS) or reading.hasManuscript('35'):
        return False

    g_counts = {}
    nonref_count = reading.countNonRefGreekManuscriptsByGroup(refMS, groupAssignments, g_counts)

    if nonref_count == 0:
        return False

    base_mss = []
    base_mss.append('28')
    base_mss.append('2542')
    for ms, gp in groupAssignments.iteritems():
        if gp in Util.CORE_GROUPS and gp != group['name']:
            base_mss.append(ms)

    if set(base_mss) & set(reading.manuscripts):
        return False

    member_count = 0
    for ms in group['members']:
        if reading.hasManuscript(ms):
            member_count = member_count + 1

    if member_count < group['minOccurs']:
        return False

    return True

def refListToString(ref_list):
    r_str = ''
    r_map = {}
    r_list = []
    for ref in ref_list:
        if not r_map.has_key(ref):
            r_map[ref] = 1
            r_list.append(ref)
        else:
            r_map[ref] = r_map[ref] + 1
    for ref in r_list:
        if r_map.has_key(ref) and r_map[ref] > 1:
            ref = ref + ' (' + str(r_map[ref]) + 'x)'
        if r_str:
            r_str = r_str + '; '
        r_str = r_str + ref
    return r_str

def readingsToString(vu, reading):
    m_reading = vu.getReadingForManuscript('35')
    readings_str = ''
    readings_str = readings_str + reading.getDisplayValue()
    if m_reading:
        readings_str = readings_str + ' | ' + m_reading.getDisplayValue()
    for rdg in vu.readings:
        if rdg == reading or rdg == m_reading or not rdg.manuscripts:
            continue

        if len(readings_str) > 0:
            readings_str = readings_str + ' | '
        readings_str = readings_str + rdg.getDisplayValue()
    return readings_str

def mssListToString(mss_list):
    mss_list = sorted(mss_list, cmp=sortMSS)

    g_list = []
    l_list = []
    has_19A = False
    has_vg = False
    for ms in mss_list:
        if ms[:2] == 'VL':
            l_list.append(ms[2:])
        elif ms == '19A':
            has_19A = True
        else:
            if ms == 'vg':
                has_vg = True
            else:
                g_list.append(ms)

    if has_19A:
        l_list.append('19A')

    mss_str = ''
    if len(g_list) > 0:
        mss_str = ' '.join(g_list)

    if len(l_list) > 0:
        if len(mss_str) > 0:
            mss_str = mss_str + ' '
        mss_str = mss_str + 'VL(' + ' '.join(l_list) + ')'

    if has_vg:
        if len(mss_str) > 0:
            mss_str = mss_str + ' '
        mss_str = mss_str + 'vg'

    return mss_str

def groupMapToString(g_map, g_list):
    g_str = ''

    Util.group_map = g_map
    if g_list:
        g_list = sorted(g_list, cmp=sortGroups)

    for item in g_list:
        ch = item[:1]
        if g_str:
            g_str = g_str + ' '
        if ch in Util.g_prefixes:
            group_list = sorted(g_map[item], cmp=sortMSS)
            g_str = g_str + '('
            ms_str = ''
            for ms in group_list:
                if ms_str:
                    ms_str = ms_str + ' '
                ms_str = ms_str + ms
            g_str = g_str + ms_str + ')'
        else:
            g_str = g_str + item
    return g_str

def mssGroupListToString(mss_list, msGroups, g_map, excludeMS):
    mss_list = sorted(mss_list, cmp=sortMSS)

    # make g_map if null
    if not g_map:
        g_map = {}
        multi_mss = []
        for ms in mss_list:
            if excludeMS and excludeMS == ms:
                continue

            if not msGroups.has_key(ms): # Latins and non-config'ed Greeks excluded
                continue

            group_parts = msGroups[ms].split(',')
            if len(group_parts) > 1:
                multi_mss.append((ms, msGroups[ms]))
                continue

            group = getGroupBase(msGroups[ms])
            if group != 'Iso' and group != 'CP45':
                if not g_map.has_key(group):
                    g_map[group] = []
                    g_map[group].append(ms)
                else:
                    g_map[group].append(ms)

        for multi in multi_mss:
            ms = multi[0]
            group_parts = multi[1].split(',')
            has_group = False
            for group in group_parts:
                group = getGroupBase(group)
                if g_map.has_key(group):
                    g_map[group].append(ms)
                    has_group = True
                    break

            if not has_group:
                group = getGroupBase(group_parts[0])
                g_map[group] = []
                g_map[group].append(ms)

    g_list = []
    l_list = []
    group_list = []
    group_map = {}
    has_19A = False
    has_vg = False
    for ms in mss_list:
        if ms[:2] == 'VL':
            l_list.append(ms[2:])
            continue
        if ms == '19A':
            has_19A = True
            continue
        if ms == 'vg':
            has_vg = True
            continue
        if msGroups[ms] == 'Iso' and msGroups[ms] == 'CP45':
            g_list.append(ms)
            continue
        grp = msGroups[ms]
        if not g_map.has_key(grp) or not g_map[grp] or len(g_map[grp]) == 1:
            g_list.append(ms)
            continue
        group_map[grp] = g_map[grp]
        if not grp in group_list:
            group_list.append(grp)

    if has_19A:
        l_list.append('19A')

    mss_str = ''
    if g_list:
        if group_list:
            group_list.extend(g_list)
        else:
            group_list = g_list

    if group_list:
        if mss_str:
            mss_str = mss_str + ' '
        mss_str = mss_str + groupMapToString(group_map, group_list)

    if l_list:
        if mss_str:
            mss_str = mss_str + ' '
        mss_str = mss_str + 'VL(' + ' '.join(l_list) + ')'

    if has_vg:
        if len(mss_str) > 0:
            mss_str = mss_str + ' '
        mss_str = mss_str + 'vg'

    return mss_str

def sortGroups(g1, g2):
    c1 = g1[:1]
    c2 = g2[:1]

    m1 = g1
    if c1 in Util.g_prefixes:
        glist1 = sorted(Util.group_map[g1], cmp=sortMSS)
        m1 = glist1[0]

    m2 = g2
    if c2 in Util.g_prefixes:
        glist2 = sorted(Util.group_map[g2], cmp=sortMSS)
        m2 = glist2[0]

    return sortMSS(m1, m2)

def sortMSS(ms1, ms2):
    if ms1 == ms2:
        raise ValueError('Duplicate witness in list %s' % ms1)

    if ms1 in Util.MS_OVERLAYS and not ms2 in Util.MS_OVERLAYS:
        return -1
    elif ms2 in Util.MS_OVERLAYS and not ms1 in Util.MS_OVERLAYS:
        return 1
    else:
        if ms1 in Util.MS_OVERLAYS and ms2 in Util.MS_OVERLAYS:
            if Util.MS_OVERLAYS.index(ms1) < Util.MS_OVERLAYS.index(ms2):
                return -1
            elif Util.MS_OVERLAYS.index(ms1) > Util.MS_OVERLAYS.index(ms2):
                return 1

    ms1 = ms1.lower()
    ms2 = ms2.lower()

    if ms1 == '19a':
        ms1 = 'vl19'
    if ms2 == '19a':
        ms2 = 'vl19'

    c1 = ms1[:1]
    c2 = ms2[:1]

    if c1 == 'v' and c2 != 'v':
        return 1
    elif c1 != 'v' and c2 == 'v':
        return -1

    if c1 == 'v' and c2 == 'v':
        if ms2 == 'vg':
            return -1
        elif ms1 == 'vg':
            return 1

        n1 = int(ms1[2:])
        n2 = int(ms2[2:])
        if n1 < n2:
            return -1
        else:
            return 1

    if c1 == 'p' and c2 != 'p':
        return -1
    elif c1 != 'p' and c2 == 'p':
        return 1

    if c1 == 'p' and c2 == 'p':
        n1 = int(ms1[1:])
        n2 = int(ms2[1:])
        if n1 < n2:
            return -1
        else:
            return 1

    if c1 == '0' and c2 != '0':
        return -1
    elif c1 != '0' and c2 == '0':
        return 1

    if c1 == '0' and c2 == '0':
        n1 = int(ms1[1:])
        n2 = int(ms2[1:])
    else:
        n1 = int(ms1)
        n2 = int(ms2)

    if n1 < n2:
        return -1
    else:
        return 1

    return 0

def sortVariations(v1, v2):
    chapter1 = None
    chapter2 = None

    label1 = v1['wrapped'].variationUnit.label
    label2 = v2['wrapped'].variationUnit.label

    # separate chapter from remaining label if present
    search1 = re.search(r'^(\d{1,2})\.(\d{1,2}\..+)$', label1)
    if search1:
        chapter1 = search1.group(1)
        label1 = search1.group(2)

    search2 = re.search(r'^(\d{1,2})\.(\d{1,2}\..+)$', label2)
    if search2:
        chapter2 = search2.group(1)
        label2 = search2.group(2)

    # different chapters, if chapter defined?
    if chapter1 and chapter2:
        if (int(chapter1) < int(chapter2)):
            return -1
        elif (int(chapter1) > int(chapter2)):
            return 1

    parts1 = makeParts(label1)
    parts2 = makeParts(label2)

    p1 = parts1[0]
    p2 = parts2[0]

    # different verses?
    if (int(p1['verse']) < int(p2['verse'])):
        return -1
    elif (int(p1['verse']) > int(p2['verse'])):
        return 1

    # different addresses?
    a1 = int(p1['addresses'][0])
    a2 = int(p2['addresses'][0])
    if a1 < a2:
        return -1
    elif a1 > a2:
        return 1

    # different number of parts?
    if len(p1) < len(p2):
        return -1
    elif len(p1) > len(p2):
        return 1

    # different number of addresses
    if len(p1['addresses']) < len(p2['addresses']):
        return -1
    elif len(p1['addresses']) > len(p2['addresses']):
        return 1

    return 0

def isSubSingular(subsingularVariants, vu, ms):
    reading = vu.getReadingForManuscript(ms)
    if not reading:
        return False

    if ms == '05':
        ss_list = subsingularVariants.split('|')
        if vu.label in ss_list:
            return True
    else:
        if len(reading.manuscripts) == 2:
            return True

    return False

def computeLayer(latinCore, latinMulti, ref_ms, vu_label, reading):
    if reading.hasManuscript('35'):
        return 'M'
    core_list = latinCore.split('|')
    multi_list = latinMulti.split('|')
    if ref_ms == '05':
        if vu_label in core_list or vu_label in multi_list:
            return 'L'
        else:
            return 'G'
    else:
        for ms in reading.manuscripts:
            if ms == s.refMS:
                continue

            if ms[:1] == 'v' or ms[:1] == 'V' or ms == '19A':
                if ms[:2] == 'VL': ms = ms[2:]
                latin_mss.append(ms)
            else:
                greek_mss.append(ms)

    return 'L' if isLatinLayer(len(greek_mss), len(latin_mss)) else 'G'

def isLatinLayer(greek_counter, latin_counter):
    is_latin = False
    #if latin_counter >= 10 and greek_counter == 5:
    #    is_latin = True
    #elif latin_counter >= 8 and greek_counter == 4:
    #    is_latin = True
    #return is_latin

    is_latin = False
    if latin_counter >= greek_counter and latin_counter > 2 and greek_counter <= 3:
        is_latin = True
    else:
        if latin_counter >= greek_counter and latin_counter > 1 and greek_counter <= 2:
            is_latin = True
        elif latin_counter >= greek_counter and latin_counter > 0 and greek_counter <= 1:
            is_latin = True
    return is_latin

def sortHauptlisteD(mi1, mi2):
    pc1 = mi1['D_ratio']
    pc2 = mi2['D_ratio']
    if pc1 < pc2:
        return 1
    elif pc1 > pc2:
        return -1

    i1 = abs(mi1['D_instance_count'])
    i2 = abs(mi2['D_instance_count'])
    if i1 < i2:
        return 1
    elif i1 > i2:
        return -1

    if mi1.has_key('D_ratio_delta') and mi2.has_key('D_ratio_delta'): 
        d1 = abs(mi1['D_ratio_delta'])
        d2 = abs(mi2['D_ratio_delta'])
        if d1 < d2:
            return 1
        elif d1 > d2:
            return -1

    return 0

def sortHauptlisteL(mi1, mi2):
    pc1 = mi1['L_ratio']
    pc2 = mi2['L_ratio']
    if pc1 < pc2:
        return 1
    elif pc1 > pc2:
        return -1

    i1 = abs(mi1['L_instance_count'])
    i2 = abs(mi2['L_instance_count'])
    if i1 < i2:
        return 1
    elif i1 > i2:
        return -1

    if mi1.has_key('L_ratio_delta') and mi2.has_key('L_ratio_delta'): 
        d1 = abs(mi1['L_ratio_delta'])
        d2 = abs(mi2['L_ratio_delta'])
        if d1 < d2:
            return 1
        elif d1 > d2:
            return -1

    return 0
