import web, os, json, re

from object.analyzer import *
from object.jsonDecoder import *
from object.qcaRunner import *
from object.queryEngine import *
from object.rangeManager import *
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
        args['dirs'] = Util().listDirs(s.config.get('statsDirs')[0])
        args['keys'] = sorted(args['dirs']['directoryMap'], cmp=sortLabels)
        args['prefix'] = 'c'
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
        args['dirs'] = Util().listDirs(s.config.get('statsDirs')[0])
        args['keys'] = sorted(args['dirs']['directoryMap'], cmp=sortLabels)
        args['prefix'] = 'c'
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

    def switchDir(s):
        udata = web.input()

        args = {}
        args['config'] = s.config
        args['dirs'] = Util().listDirs(udata.statsdir)
        try:
            args['keys'] = sorted(args['dirs']['directoryMap'], cmp=sortLabels)
        except AttributeError, e:
            args['keys'] = sorted(args['dirs']['directoryMap'], cmp=sortSegments)
        args['prefix'] = 'c' if 'stats' in udata.statsdir else ''
        
        fragment = s.templates.dirlist(args)

        return fragment

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

    def viewbinary(s):
        jsonfile = s.config.get('finderFolder') + 'c01-16-binary-variants.json'
        with open(jsonfile, 'r') as file:
            jdata = file.read()
            file.close()
        j_load = json.loads(jdata)
        j_load['title'] = 'Binary'
        return s.templates.viewmultiple(j_load)

    def viewbinarydl(s):
        jsonfile = s.config.get('finderFolder') + 'c01-16-binaryDL-variants.json'
        with open(jsonfile, 'r') as file:
            jdata = file.read()
            file.close()
        j_load = json.loads(jdata)
        j_load['title'] = 'DL'
        return s.templates.viewmultiple(j_load)

    def viewmultiple(s):
        jsonfile = s.config.get('finderFolder') + 'c01-16-multiple-variants.json'
        with open(jsonfile, 'r') as file:
            jdata = file.read()
            file.close()
        j_load = json.loads(jdata)
        j_load['title'] = 'Multiple'
        return s.templates.viewmultiple(j_load)

    def viewsegments(s):
        udata = web.input()
        jsonfile = s.config.get('dicerFolder') + udata.referencems + '-' + udata.segcfg + '-hauptliste.json'
        with open(jsonfile, 'r') as file:
            jdata = file.read()
            file.close()
        return s.templates.viewsegments(json.loads(jdata))

    def startFinder(s):
        q_file = s.config.get('finderFolder') + '/query-results/saved-queries.json'
        with open(q_file, 'r') as file:
            jdata = file.read()
            file.close()
        jmap = json.loads(jdata)
        jmap['json_string'] = jdata
        return s.templates.finderui(jmap)

    def fetchresult(s):
        udata = web.input()

        # load query results
        r_file = s.config.get('finderFolder') + '/query-results/' + udata.result_id + '.json'
        with open(r_file, 'r') as file:
            jdata = file.read()
            file.close()
        qmap = json.loads(jdata)

        # load query stats
        r_file = s.config.get('finderFolder') + '/query-results/' + udata.result_id + '-stats.json'
        with open(r_file, 'r') as file:
            jdata = file.read()
            file.close()
        smap = json.loads(jdata)

        jmap = {
          'query_results': qmap,
          'stats_results': smap
        }

        return s.templates.queryresults(jmap)

    def query(s):
        udata = web.input()

        refMSS = []
        for key in udata:
            if key[:3] == 'rms':
                refMSS.append(key[3:])

        reading_forms = []
        if udata.reading_forms:
            forms = udata.reading_forms.split(',')
            for form in forms:
                reading_forms.append(form)

        variant_forms = []
        if udata.variant_forms:
            forms = udata.variant_forms.split(',')
            for form in forms:
                variant_forms.append(form)

        layers = []
        if udata.layer_M == '1':
            layers.append('M')
        if udata.layer_D == '1':
            layers.append('D')
        if udata.layer_L == '1':
            layers.append('L')

        is_lemma = False
        if udata.is_lemma == '1':
            is_lemma = True

        query = {
          'name': udata.name,
          'generated_id': udata.generated_id,
          'generated_name': udata.generated_name,
          'reading_forms': reading_forms,
          'read_op': udata.read_op,
          'variant_forms': variant_forms,
          'var_op': udata.var_op,
          'layers': layers,
          'is_lemma': is_lemma
        }

        q_file = s.config.get('finderFolder') + '/query-results/saved-queries.json'

        with open(q_file, 'r') as file:
            jdata = file.read()
            file.close()

        saved_queries = json.loads(jdata)

        # Update recent queries
        recent_queries = []
        for q in saved_queries['recent_queries']:
            if saved_queries['query_map'].has_key(q) and q != udata.generated_id:
                recent_queries.append(q)

        recent_queries.append(udata.generated_id)
        saved_queries['recent_queries'] = recent_queries
        saved_queries['query_map'][udata.generated_id] = query

        # Run query
        query_engine = QueryEngine()
        query_engine.refMS = refMSS[0]
        query_engine.queryCriteria = query
        query_engine.findMatches()

        # Update recent results
        recent_results = []
        for result in saved_queries['recent_results']:
            result_id = result['result_id']
            if result_id != refMSS[0] + udata.generated_id:
                recent_results.append(result)

        result = {
            'result_id': refMSS[0] + udata.generated_id,
            'query_name': udata.generated_name,
            'ref_ms': refMSS[0]
        }
        recent_results.append(result)
        saved_queries['recent_results'] = recent_results

        # Save recent queries, recent results, and query criteria
        jdata = json.dumps(saved_queries, ensure_ascii=False)
        with open(q_file, 'w+') as file:
            file.write(jdata.encode('UTF-8'))
            file.close()

        # load query results
        r_file = s.config.get('finderFolder') + '/query-results/' + refMSS[0] + query['generated_id'] + '.json'
        with open(r_file, 'r') as file:
            jdata = file.read()
            file.close()
        qmap = json.loads(jdata)

        # load query stats
        r_file = s.config.get('finderFolder') + '/query-results/' + refMSS[0] + query['generated_id'] + '-stats.json'
        with open(r_file, 'r') as file:
            jdata = file.read()
            file.close()
        smap = json.loads(jdata)

        jmap = {
          'query_results': qmap,
          'stats_results': smap
        }

        return s.templates.queryresults(jmap)

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
