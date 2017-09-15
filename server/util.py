import os, json, re

from utility.config import *

def sortLabels(lab1, lab2):
    r1 = 'c' + re.search(r'^Mark (\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab1).group(1)
    r2 = 'c' + re.search(r'^Mark (\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab2).group(1)

    pos1 = 1000
    ranges = Util().config.get('ranges')
    if r1 in ranges:
        pos1 = ranges.index(r1)

    pos2 = 1000
    ranges = Util().config.get('ranges')
    if r2 in ranges:
        pos2 = ranges.index(r2)

    if pos1 < pos2:
        return -1
    elif pos1 > pos2:
        return 1

    ms1 = re.search(r'^Mark (\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab1).group(2)
    ms2 = re.search(r'^Mark (\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab2).group(2)

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
            return 1
        elif ms1[:1] != 'v' and ms2[:1] == 'v':
            return -1

    cod1 = re.search(r'^Mark (\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab1).group(3)
    cod2 = re.search(r'^Mark (\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab2).group(3)

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
