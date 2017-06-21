import web

from utility.config import *

from server.util import *

class Index:
    def __init__(s):
        s.config = Config('web-config.json')
        s.templates = web.template.render('templates/')

    def GET(s):
        args = {}
        args['config'] = s.config
        args['dirs'] = Util().listDirs()

        return s.templates.index(args)
