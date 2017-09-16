import web, os, json, re

from object.analyzer import *
from object.jsonDecoder import *
from object.qcaRunner import *
from object.util import *

from utility.config import *

from server.util import *
from server.kmap import *

def sortWitnesses(w1, w2):
    if (int(w1['occurrences']) > int(w2['occurrences'])):
        return -1
    elif (int(w1['occurrences']) < int(w2['occurrences'])):
        return 1
    else:
        return 0

class Controller:
    def __init__(s):
        s.config = Config('web-config.json')
        s.templates = web.template.render('templates/', globals={'re': re, 'str': str, 'KMap': KMap })

    def GET(s, operation):
        method = getattr(s, operation, lambda: "")
        return method()

    def POST(s, operation):
        method = getattr(s, operation, lambda: "")
        return method()

    # actions
    def boolanalyze(s):
        udata = web.input()
        refMSS = []
        for key in udata:
            if key[:3] == 'rms':
                refMSS.append(key[3:])
        QCARunner().analyze(udata.chapter, udata.inputrange, refMSS, udata.qcaset)

        args = {}
        args['config'] = s.config
        args['dirs'] = Util().listDirs()
        args['keys'] = sorted(args['dirs']['directoryMap'], cmp=sortLabels)
        fragment = s.templates.dirlist(args)

        return fragment

    def clustanalyze(s):
        udata = web.input()
        refMSS = []
        for key in udata:
            if key[:3] == 'rms':
                refMSS.append(key[3:])
        Analyzer().analyze(udata.chapter, udata.inputrange, refMSS)

        args = {}
        args['config'] = s.config
        args['dirs'] = Util().listDirs()
        args['keys'] = sorted(args['dirs']['directoryMap'], cmp=sortLabels)
        fragment = s.templates.dirlist(args)

        return fragment

    def clustmerge(s):
        result = s.getJSONResult()
        return s.templates.clustmerge(result)

    def witnessdistribmerge(s):
        result = s.getJSONResult()
        return s.templates.witnessdistribmerge(result)

    def clustresults(s):
        result = s.getJSONResult()
        return s.templates.clustresults(result)

    def findVariants(s):
        finderDir = s.config.get('finderFolder')
        jsonfile = finderDir + '/c01-16-variants.json'
        with open(jsonfile, 'r') as file:
            jdata = file.read()
            file.close()
        jmap = json.loads(jdata, cls=ComplexDecoder)
        return s.templates.rendervariants(jmap)

    def witnessdistrib(s):
        result = s.getJSONResult()
        return s.templates.witnessdistrib(result)

    def kmap(s):
        udata = web.input()
        booldir = s.config.get('boolDir')
        subdir = re.search(r'\-([a-zA-Z0-9]+)$', udata.dir).group(1)
        jsonfile = booldir + subdir + '/' + udata.filebase + '-results.json'
        with open(jsonfile, 'r') as file:
            jdata = file.read()
            file.close()

        jmap = json.loads(jdata)
        jmap['set'] = subdir
        jmap['configuration'] = udata.filebase
        dims = len(jmap['manuscripts'])
        if dims < 6 or dims > 10:
            raise ValueError('Number of MSS must be between 6 and 10')

        return s.templates.kmap(jmap)

    # non-actions
    def getJSONResult(s):
        result = None
        udata = web.input()
        if udata.has_key('json'):
            jsondata = udata['json']
            result = json.loads(jsondata)
            for clust in result['clusters']:
                if clust.has_key('witnesses'):
                    clust['witnesses'] = sorted(clust['witnesses'], cmp=sortWitnesses)
        return result