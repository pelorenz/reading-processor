#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, argparse, urllib, subprocess, string, re, shutil, datetime, operator, json

from utility.config import *

class QCARunner:

    def __init__(s):
        s.chapter = ''
        s.inputfile = ''
        s.refMSS = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print info

    def analyze(s, chapter, inputfile, refMSS):
        c = s.config = Config('processor-config.json')

        s.info('Calling analysis with chapter', chapter, 'and input file', inputfile)
        s.info('Reference MSS', refMSS)

        s.chapter = chapter
        s.inputfile = inputfile
        s.refMSS = refMSS

        for ms in refMSS:
            # boolAnalyzer.py -v -C c01 -R 032,05 -f mark-01a-all
            s.info('Calling boolAnalyzer.py with', refMSS)
            p = ['boolAnalyzer.py']
            p.append('-v')
            p.append('-C')
            p.append(s.chapter)
            p.append('-R')
            p.append(s.refMSS)
            p.append('-f')
            p.append(s.inputfile)
            proc = subprocess.Popen(p, stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()

            # Initialize Python 3.6 environment
            py3_env = os.environ.copy()
            py3_env['PYTHONPATH'] = 'C:\Dev\Python36\Lib;'
            py3_env['PY_PYTHON'] = '3'
            py3_env['PATH'] = 'C:\Dev\python36;C:\Dev\python36\Scripts;'
            
            # qcaAnalyzer.py -v -f c01-05
            s.info('Calling qcaAnalyzer.py with', refMSS)
            p = ['qcaAnalyzer.py']
            p.append('-v')
            p.append('-f')
            p.append(s.chapter + '-' + ms)
            proc = subprocess.Popen(p, env=py3_env, stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
        s.info('Done')
