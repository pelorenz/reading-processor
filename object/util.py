import sys, os

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

def sortVariations(v1, v2):
    parts1 = makeParts(v1['wrapped'].variationUnit.label)
    parts2 = makeParts(v2['wrapped'].variationUnit.label)

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
