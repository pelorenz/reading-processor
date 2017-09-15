#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, argparse, urllib, subprocess, string, re, shutil, datetime, operator, json

from utility.config import *

class QCARunner:

    def __init__(s):
        s.chapter = ''
        s.inputrange = ''
        s.qcaset = ''
        s.refMSS = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print info

    def analyze(s, chapter, inputrange, refMSS, qcaset):
        c = s.config = Config('processor-config.json')

        s.info('Calling analysis with chapter', chapter, 'and input range', inputrange)
        s.info('Reference MSS', refMSS)

        s.chapter = chapter
        s.inputrange = inputrange
        s.qcaset = qcaset
        s.refMSS = refMSS

        for ms in refMSS:
            # TTMaker.py -v -C c01 -R 032,05 -f mark-01a-all
            s.info('Calling TTMaker.py with', refMSS)
            p = ['TTMaker.py']
            p.append('-v')
            p.append('-a')
            p.append(s.inputrange)
            p.append('-R')
            p.append(s.refMSS)
            p.append('-q')
            p.append(s.qcaset)
            proc = subprocess.Popen(p, stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()

            # Initialize Python 3.6 environment
            py3_env = os.environ.copy()
            py3_env['PYTHONPATH'] = 'C:\Dev\Python36\Lib;'
            py3_env['PY_PYTHON'] = '3'
            py3_env['PATH'] = 'C:\Dev\python36;C:\Dev\python36\Scripts;'
            
            # TTMinimizer.py -v -f c01-05
            s.info('Calling TTMinimizer.py with', refMSS)
            p = ['TTMinimizer.py']
            p.append('-v')
            p.append('-f')
            p.append(s.chapter + '-' + ms)
            p.append('-q')
            p.append(s.qcaset)
            proc = subprocess.Popen(p, env=py3_env, stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
        s.info('Done')
