#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, argparse, urllib, subprocess, string, re, shutil, datetime, operator, json

from utility.config import *
from utility.options import *

from object.jsonDecoder import *

class JSONProcessor:

    def __init__(s):
        # all addresses
        s.addresses = []
        s.jsondata = []

    def info(s, *args):
        info = ''
        if s.options.verbose:
            for i, arg in enumerate(args):
                if i > 0: info += ' '
                info += str(arg).strip()
            print info

    def processJSON(s, filename):
        c = s.config
        o = s.options
        s.info('processing', filename)

        # load data
        jsondata = ''
        jsonfile = c.get('outputFolder') + str(filename)
        with open(jsonfile, 'r') as file:
            s.info('reading', filename)
            jsondata = file.read().decode('utf-8')
            s.jsondata.append(jsondata)
            file.close()

        result = json.loads(jsondata, cls=ComplexDecoder)
        Address.max_forms = result['max_forms']
        Address.max_non_sing = result['max_non_sing']
        s.addresses.append(result['addresses'])

    def render(s, filename):
        c = s.config
        o = s.options

        parts = filename.split('.')
        if len(parts) <> 2:
            return

        # load html initial fragment
        s.htmldata = ''
        inithtml = c.get('htmlFolder') + c.get('htmlInitialFragment')
        with open(inithtml, 'r') as file:
            s.info('reading', inithtml)
            s.htmldata = file.read().decode('utf-8')
            file.close()

        # set corresponding model in HTML
        s.htmldata = s.htmldata.replace('<FILENAME>', parts[0])

        # create JS model file
        jsmodel = c.get('htmlFolder') + 'js/model-' + parts[0] + '.js'
        with open(jsmodel, 'w+') as file:
            file.write('DSS.models = [];')
            for i in range(0, len(s.jsondata)):
                file.write('DSS.models[' + str(i) + '] = JSON.parse(\''.encode('utf-8'))
                file.write(s.jsondata[i].encode('utf-8'))
                file.write('\');')
            file.write('DSS.buildObjects();')
            file.close()

        # build html file
        outputfile = c.get('htmlFolder') + parts[0] + '.htm'
        with open(outputfile, 'w+') as file:
            file.write(s.htmldata.encode('utf-8'))
            file.close()

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        if o.file:
            files = [o.file + '.json', o.file + '-lat.json']
        else:
            files = c.get('jsonFiles')

        if (files):
            for filename in files:
                s.processJSON(filename)
            s.render(files[0])

# DON'T RUN DIRECTLY - CALL csvProcessor.py -v -f [filename minus suffix]
# Invoke via entry point
# jsonProcessor.py -v > out2.txt
JSONProcessor().main(sys.argv[1:])
