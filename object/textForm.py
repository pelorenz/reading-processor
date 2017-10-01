#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json, re, urllib2
import xml.etree.ElementTree
from argparse import Namespace

class  TextForm(object):

    # Perseus url
    MORPH_URL = 'http://www.perseus.tufts.edu/hopper/xmlmorph?'

    # Morphological forms to ignore
    IGNORE_MORPHS = [u'α', u'αι', u'αν', u'αρια', u'cum', u'δε', u'δια', u'ε', u'εις', u'εν', u'εως', u'η', u'ης', u'θ', u'θυ', u'ι', u'ιην', u'ιης', u'ιν', u'ινα', u'ις', u'και', u'κα', u'καθ', u'μαρια', u'maria', u'μη', u'οι', u'ουν', u'τη', u'την', u'τον', u'τω', u'υν', u'ω', u'ως']

    # morphological cache
    morph_cache = {}

    def __init__(s, f, lang, mstr, lstr, doLookup):
        # canonical form
        s.form = f

        # language
        s.language = lang

        # linked manuscripts
        s.linked_mss = []

        # morph str
        s.morphstr = mstr

        # lemma str
        s.lemmastr = lstr

        # morphology data
        s.morphs = {}

        if doLookup:
            if not f:
                return

            if (TextForm.morph_cache.has_key(f)):
                s.morphs = TextForm.morph_cache[f]
            else:
                # call morpheus to get parsing
                url = TextForm.MORPH_URL
                if (lang == 'latin'):
                    url = url + 'lang=la&lookup='
                else:
                    url = url + 'lang=greek&lookup='

                f = s.to_betacode(f)

                # Do lookup
                url = url + urllib2.quote(f.encode('UTF-8'))
                try:
                    print('Request ... ')
                    response = urllib2.urlopen(url)
                except urllib2.HTTPError as err:
                    print('HTTP error ... ', err.reason)
                except urllib2.URLError as err:
                    print('URL error ... ', err.reason)
                    #print 'Second request ... ' 
                    #response = urllib2.urlopen(url)
                except urllib2.HTTPException as err:
                    print('HTTP exception ... ', err.reason)

                analyses = response.read()

                # Parse XML
                morphs = []
                doc = xml.etree.ElementTree.fromstring(analyses)
                for analysis in doc.iter(tag='analysis'):
                    map = {}
                    for element in analysis:
                        map[element.tag] = element.text
                    morphs.append(map)
                    s.morphs = morphs

                # Cache result
                TextForm.morph_cache[s.form] = morphs

            s.initMorphStrings()

    def jsonSerialize(s):
        return { 'linkedManuscripts': s.linked_mss, 'form': s.getForm(), 'language': s.language, '_type': 'textForm', 'morph': s.morphstr, 'lemma': s.lemmastr }

    def getForm(s):
        if not s.form:
            return 'om.'
        else:
            return s.form

    def getLemmas(s):
        lemmas = []
        if not s.form or not TextForm.morph_cache:
            return lemmas

        if not TextForm.morph_cache.has_key(s.form):
            return lemmas

        if s.isIgnoreMorph(s.form):
            return lemmas

        morphs = TextForm.morph_cache[s.form]
        for morph in morphs:
            if morph.has_key('lemma') and not morph['lemma'] in lemmas:
                lemmas.append(morph['lemma'])

        return lemmas

    def concatManuscripts(s):
        return ' '.join([ms.displayId for ms in s.linked_mss])

    def isIgnoreMorph(s, frm):
        for mph in TextForm.IGNORE_MORPHS:
            if mph == frm:
                return True
        return False

    def initMorphStrings(s):
        # Remove problem forms
        if s.isIgnoreMorph(s.form):
            return

        morphkeys = {}
        #has_digits = re.compile('\d')
        for m in s.morphs:
            #if bool(has_digits.search(m['lemma'])):
            #    continue

            if m.has_key('number') and m['number'] == 'dual':
                continue

            if m.has_key('case') and m['case'] == 'voc':
                continue

            keypart = ''
            gennumpart = ''
            if m['pos'] == 'verb':
                if m.has_key('person'):
                    gennumpart = gennumpart + m['person'][0]
                if m.has_key('number'):
                    gennumpart = gennumpart + m['number'][0]

                if m.has_key('tense'):
                    tense = m['tense']
                    if tense == 'imperf':
                        tense = 'impf'
                    keypart = keypart + tense.upper()
                if m.has_key('mood'):
                    mood = m['mood']
                    if mood == 'imperat':
                        mood = 'impv'
                    keypart = keypart + '.' + mood
                if m.has_key('voice'):
                    keypart = keypart + '.' + m['voice']
            elif m['pos'] == 'part':
                if m.has_key('gender'):
                    gennumpart = gennumpart + m['gender'][0]
                if m.has_key('number'):
                    gennumpart = gennumpart + m['number'][0]

                if m.has_key('tense'):
                    tense = m['tense']
                    if tense == 'imperf':
                        tense = 'impf'
                    keypart = keypart + tense.upper()
                if m.has_key('case'):
                    keypart = keypart + '.' + m['case'].upper()
                if m.has_key('voice'):
                    keypart = keypart + '.' + m['voice']
            else:
                if m['pos'] == 'noun' or m['pos'] == 'adj' or m['pos'] == 'pron':
                    if m.has_key('gender'):
                        gennumpart = gennumpart + m['gender'][0]
                    if m.has_key('number'):
                        gennumpart = gennumpart + m['number'][0]

                    if m.has_key('case'):
                        keypart = keypart + m['case'].upper()

            if keypart:
                gennums = {}
                lemmas = {}
                if morphkeys.has_key(keypart):
                    gennums = morphkeys[keypart][0]
                    lemmas = morphkeys[keypart][1]
                if gennumpart:
                    gennums[gennumpart] = 'placeholder'
                lemmas[m['lemma']] = 'placeholder'
                morphkeys[keypart] = [gennums, lemmas]

        lemstr = ''
        sumstr = ''
        morphkeys = collections.OrderedDict(sorted(morphkeys.items()))
        for key in morphkeys:
            gennum = morphkeys[key][0]
            lemma = morphkeys[key][1]
            if len(sumstr) > 0:
                sumstr = sumstr + ' / '
            if len(gennum.keys()) == 0: # e.g. infinitives
                sumstr = sumstr + key
            else:
                sumstr = sumstr + '|'.join(gennum.keys()) + key
            if len(lemstr) > 0:
                lemstr = lemstr + ' / '
            lemstr = lemstr + '|'.join(lemma.keys())

        s.morphstr = sumstr
        s.lemmastr = lemstr

    def to_betacode(s, str):
        betastr = ''
        for ch in str:
            if ch == u'α':
                betastr = betastr + 'a'
                continue
            if ch == u'β':
                betastr = betastr + 'b'
                continue
            if ch == u'γ':
                betastr = betastr + 'g'
                continue
            if ch == u'δ':
                betastr = betastr + 'd'
                continue
            if ch == u'ε':
                betastr = betastr + 'e'
                continue
            if ch == u'ζ':
                betastr = betastr + 'z'
                continue
            if ch == u'η':
                betastr = betastr + 'h'
                continue
            if ch == u'θ':
                betastr = betastr + 'q'
                continue
            if ch == u'ι':
                betastr = betastr + 'i'
                continue
            if ch == u'κ':
                betastr = betastr + 'k'
                continue
            if ch == u'λ':
                betastr = betastr + 'l'
                continue
            if ch == u'μ':
                betastr = betastr + 'm'
                continue
            if ch == u'ν':
                betastr = betastr + 'n'
                continue
            if ch == u'ξ':
                betastr = betastr + 'c'
                continue
            if ch == u'ο':
                betastr = betastr + 'o'
                continue
            if ch == u'π':
                betastr = betastr + 'p'
                continue
            if ch == u'ρ':
                betastr = betastr + 'r'
                continue
            if ch == u'σ':
                betastr = betastr + 's'
                continue
            if ch == u'ς':
                betastr = betastr + 's'
                continue
            if ch == u'τ':
                betastr = betastr + 't'
                continue
            if ch == u'υ':
                betastr = betastr + 'u'
                continue
            if ch == u'φ':
                betastr = betastr + 'f'
                continue
            if ch == u'χ':
                betastr = betastr + 'x'
                continue
            if ch == u'ψ':
                betastr = betastr + 'y'
                continue
            if ch == u'ω':
                betastr = betastr + 'w'
                continue
            betastr = betastr + ch

        return betastr

