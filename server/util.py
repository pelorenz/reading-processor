import os, json

from utility.config import *

def sortLabels(l1, l2):
    if '-03' in l1 and '-03' in l2:
        if '038' in l1:
            return 1
        elif '038' in l2:
            return -1

        if '032' in l1:
            return 1
        elif '032' in l2:
            return -1

        # should never happen
        return 0
    else:
        if l1 < l2:
            return -1
        elif l2 < l1:
            return 1
        else:
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
