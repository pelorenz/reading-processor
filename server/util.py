import os, json, re

from object.jsonDecoder import *

from utility.config import *

def sortLabels(lab1, lab2):
    i1 = 'c' + re.search(r'^([A-Za-z ]+)(\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab1).group(1)
    i2 = 'c' + re.search(r'^([A-Za-z ]+)(\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab2).group(1)

    if i1 < i2:
        return -1
    elif i1 > i2:
        return 1

    r1 = 'c' + re.search(r'^([A-Za-z ]+)(\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab1).group(2)
    r2 = 'c' + re.search(r'^([A-Za-z ]+)(\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab2).group(2)

    pos1 = 1000
    ranges = Util().config.get('ranges')
    if r1 in ranges:
        pos1 = ranges.index(r1)

    pos2 = 1000
    if r2 in ranges:
        pos2 = ranges.index(r2)

    if pos1 < pos2:
        return -1
    elif pos1 > pos2:
        return 1

    ms1 = re.search(r'^([A-Za-z ]+)(\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab1).group(3)
    ms2 = re.search(r'^([A-Za-z ]+)(\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab2).group(3)

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

    cod1 = re.search(r'^([A-Za-z ]+)(\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab1).group(4)
    cod2 = re.search(r'^([A-Za-z ]+)(\d{2,2}\-{0,1}\d{0,2})(\-\d{1,4})([A-Z].*)$', lab2).group(4)

    if cod1 < cod2:
        return -1
    elif cod1 > cod2:
        return 1

    return 0

def sortSegments(lab1, lab2):
    # Extract ref MS from label
    rx = r'^Mark (\d{1,2},\d{1,2}\-\d{1,2},\d{1,2})\-(\d{2,3})QCA\-[A-Za-z]+$'

    ms1 = re.search(rx, lab1).group(2)
    ms2 = re.search(rx, lab2).group(2)

    # TODO: if different MSS, sort MSS and return

    # Extract segment id from label
    si1 = re.search(rx, lab1).group(1)
    si2 = re.search(rx, lab2).group(1)

    # Load segment names from json in dicer-results
    s_list = []
    if not Util.segment_lists.has_key(ms1):
        jsonfile = Util().config.get('dicerFolder') + ms1 + '-segments.json'
        with open(jsonfile, 'r') as file:
            jdata = file.read()
            file.close()
        s_data = json.loads(jdata)
        for seg in s_data:
            s_list.append(seg['label'])
        Util.segment_lists[ms1] = s_list
    else:
        s_list = Util.segment_lists[ms1]

    # Sort by position in segment list
    pos1 = 1000
    if si1 in s_list:
        pos1 = s_list.index(si1)

    pos2 = 1000
    if si2 in s_list:
        pos2 = s_list.index(si2)

    if pos1 < pos2:
        return -1
    elif pos1 > pos2:
        return 1

    return 0

class Util:
    segment_lists = {}

    def __init__(s):
        s.config = Config('web-config.json')

    def listDirs(s, rootdir):
        # find current stats directories
        result = {}
        dirmap = {}
        statsDir = rootdir
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
