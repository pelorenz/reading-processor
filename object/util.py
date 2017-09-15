import sys, os, re

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

def sortMSS(ms1, ms2):
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
