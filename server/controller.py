import web, os, json

from object.analyzer import *
from utility.config import *

from server.util import *

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
        s.templates = web.template.render('templates/')

    def GET(s, operation):
        method = getattr(s, operation, lambda: "")
        return method()

    def POST(s, operation):
        method = getattr(s, operation, lambda: "")
        return method()

    # actions
    def analyze(s):
        udata = web.input()
        refMSS = []
        for key in udata:
            if key[:3] == 'rms':
                refMSS.append(key[3:])
        Analyzer().analyze(udata.chapter, udata.inputfile, refMSS)

        args = {}
        args['config'] = s.config
        args['dirs'] = Util().listDirs()
        fragment = s.templates.dirlist(args)

        return fragment

    def clustresults(s):
        result = s.getJSONResult()
        return s.templates.clustresults(result)

    def witnessdistrib(s):
        result = s.getJSONResult()
        return s.templates.witnessdistrib(result)

    # non-actions
    def getJSONResult(s):
        result = None
        udata = web.input()
        if udata.has_key('json'):
            jsondata = udata['json']
            result = json.loads(jsondata)
            for clust in result['clusters']:
                clust['witnesses'] = sorted(clust['witnesses'], cmp=sortWitnesses)
        return result