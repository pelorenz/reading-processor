import json

from object.jsonDecoder import *
from utility.options import *
from utility.config import *

class  Env:
    def __init__(s, cfg, opts):
        s.config = cfg
        s.options = opts

        # reference MSS
        s.refMS_IDs = s.refMSS_IDs()

        # comparison MSS
        s.comparisonMSS = cfg.get('comparisonMSS')

        # latin MSS
        s.latinMSS = cfg.get('latinMSS')

        # MSS accepted with nils
        s.nilExceptions = cfg.get('nilExceptions')

    def chapter(s):
        if type(s.options) is CommandLine and s.options.chapter:
            return s.options.chapter
        elif type(s.options) is dict and s.options.has_key('chapter'):
            return s.options['chapter']
        else:
            chapter = s.config.get('variantChapter')
            return chapter[:len(chapter) - 1]

    def inputFile(s):
        if type(s.options) is CommandLine:
            return s.options.file
        elif type(s.options) is dict and s.options.has_key('inputfile'):
            return s.options['inputfile']
        else:
            return s.config.get('variantFile')

    def loadVariants(s, varfile):
        model = ''
        with open(varfile, 'r') as file:
            model = file.read().decode('utf-8-sig') # Remove BOM
            model = model.encode('utf-8') # Reencode without BOM
            file.close()

        # Load JSON
        return json.loads(model, cls=ComplexDecoder)

    def refMSS_IDs(s):
        if type(s.options) is dict and s.options.has_key('refMSS_IDs'):
            return s.options['refMSS_IDs']
        else:
            return s.config.get('referenceMSS')

    def varFile(s):
        file = s.inputFile() + '.json'
        chapter = s.chapter() + '/'

        return s.config.get('variantFolder') + chapter + file
