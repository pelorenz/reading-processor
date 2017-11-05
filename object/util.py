import sys, os, re

class Util:
    MS_OVERLAYS = [ 'na28' ]

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
