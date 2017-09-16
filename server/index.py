import web, re

from utility.config import *

from server.util import *

class Index:
    def __init__(s):
        s.config = Config('web-config.json')
        s.templates = web.template.render('templates/', globals={'re': re})

    def GET(s):
        args = {}
        args['config'] = s.config
        args['dirs'] = Util().listDirs(s.config.get('statsDirs')[0])
        args['keys'] = sorted(args['dirs']['directoryMap'], cmp=sortLabels)
        args['prefix'] = 'c'

        return s.templates.index(args)
