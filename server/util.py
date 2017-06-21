import os, json

from utility.config import *

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
