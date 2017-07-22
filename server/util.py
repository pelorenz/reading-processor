import os, json, re

from utility.config import *

def sortLabels(lab1, lab2):
    ch1 = lab1[5:7]
    ch2 = lab2[5:7]

    ch1 = int(ch1[1:]) if ch1[:1] == '0' else int(ch1)
    ch2 = int(ch2[1:]) if ch2[:1] == '0' else int(ch2)

    ptA = lab1[7:10]
    ptB = lab2[7:10]

    ms1 = lab1[8:] if ptA[:1] != 'p' else lab1[11:]
    ms2 = lab2[8:] if ptB[:1] != 'p' else lab2[11:]

    ptA = int(ptA[2:]) if ptA[:1] == 'p' else 0
    ptB = int(ptB[2:]) if ptB[:1] == 'p' else 0

    if ch1 < ch2:
        return -1
    elif ch1 > ch2:
        return 1

    if ptA < ptB:
        return -1
    elif ptA > ptB:
        return 1

    ms1 = ms1.replace('G', '').replace('L', '').replace('D', '')
    ms2 = ms2.replace('G', '').replace('L', '').replace('D', '')

    ms1 = re.sub(r'QCA\-[a-zA-Z0-9]+', '', ms1)
    ms2 = re.sub(r'QCA\-[a-zA-Z0-9]+', '', ms2)

    if ms1[:1] == '0' and ms2[:1] != '0':
        return -1
    elif ms1[:1] != '0' and ms2[:1] == '0':
        return 1

    if ms1[:1] == '0' and ms2[:1] == '0':
        ms1 = int(ms1[1:])
        ms2 = int(ms2[1:])
        if ms1 < ms2:
            return -1
        elif ms1 > ms2:
            return 1
    elif ms1[:1].isdigit() and ms2[:1].isdigit():
        if int(ms1) < int(ms2):
            return -1
        elif int(ms1) > int(ms2):
            return 1
    else:
        if ms1[:1] == 'v' and ms2[:1] != 'v':
            return -1
        elif ms1[:1] != 'v' and ms2[:1] == 'v':
            return 1

    if 'GL' in lab1: cod1 = 'GL'
    elif 'L' in lab1: cod1 = 'L'
    else:
        if 'QCA' in lab1: cod1 = 'QCA'
        else: cod1 = 'D'

    if 'GL' in lab2: cod2 = 'GL'
    elif 'L' in lab2: cod2 = 'L'
    else:
        if 'QCA' in lab2: cod2 = 'QCA'
        else: cod2 = 'D'

    if cod1 < cod2:
        return -1
    elif cod1 > cod2:
        return 1

    return 0

class Util:
    def __init__(s):
        s.config = Config('web-config.json')

    def listDirs(s):
        # find current stats directories
        result = {}
        dirmap = {}
        statsDir = s.config.get('statsDir')
        for dir in os.listdir(statsDir):
            subdirs = []
            absdir = statsDir + dir
            for sdir in os.listdir(absdir):
                sa = absdir + '/' + sdir
                if os.path.isdir(sa):
                    if 'clusters' in sdir:
                        subdirs.append(sdir[:1])
            dirmap[dir] = subdirs
        result['directoryMap'] = dirmap
        return result
