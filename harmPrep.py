#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, re

class HarmPrep:

    book = 'J'
    infile = 'input/Jn-na27.txt'
    outfile = 'output/jn-na27-tagged.txt'

    def __init__(s):
        s.TODO = ''

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def main(s, argv):
        infile = HarmPrep.infile
        with open(infile, 'r') as file:
            s.info('reading', HarmPrep.infile)
            indata = file.read().decode('utf-8')
            file.close()

        outfile = HarmPrep.outfile
        with open(outfile, 'w+') as file:
            s.info('writing', HarmPrep.outfile)

            inlines = indata.split('\n')
            chapter = None
            for line in inlines:
                if not line:
                    continue

                if re.search(r'^(\d{1,2}) {0,1}$', line):
                    chapter = line.strip()
                    file.write((chapter + u'\n').encode('UTF-8'))
                    continue

                words = line.split(' ')
                if len(words) < 2:
                    continue

                verse = words[0]
                t_line = verse # tagged line
                for idx, word in enumerate(words):
                    if idx == 0:
                        continue # verse num

                    word = word + u' {' + HarmPrep.book + chapter + u'.' + verse + u'.' + str(idx) + u'}'
                    t_line = t_line + u'\t' + word

                file.write((t_line + u'\n').encode('UTF-8'))

            file.close()

        s.info('Done')

# Invoke via entry point
#
# harmPrep.py
HarmPrep().main(sys.argv[1:])
