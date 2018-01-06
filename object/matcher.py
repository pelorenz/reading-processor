#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, sys, os, string, re

from object.overlayManager import *
from object.readingGroup import *
from object.synopticParallel import *
from object.util import *

class Matcher:

    TYPE_CONTINUOUS = 'continuous'
    TYPE_SYNOPTIC = 'synoptic'
    TYPE_CORRECTOR_01 = 'corrector01'
    TYPE_CORRECTOR_05 = 'corrector05'

    def __init__(s, model, base_addr, slot_idx, vu, v_lookup, o_id, o_type):
        s.model = model
        s.base_addr = base_addr
        s.slot_idx = slot_idx
        s.var_unit = vu
        s.v_lookup = v_lookup
        s.overlay_id = o_id
        s.type = o_type

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        if web and hasattr(web, 'isWeb') and web.isWeb:
            web.debug(info)
        else:
            print(info) 

    def isMatch(s, r_match, r_container):
        if s.type == Matcher.TYPE_CONTINUOUS:
            return s.isContinuousMatch(r_match, r_container)
        if s.type == Matcher.TYPE_SYNOPTIC:
            return s.isSynopticMatch(r_match, r_container)
        if s.type == Matcher.TYPE_CORRECTOR_01:
            return s.isC01Match(r_match, r_container)
        if s.type == Matcher.TYPE_CORRECTOR_05:
            return s.isC05Match(r_match, r_container)
        return False

    def handleKeyError(s, e, ru_addr):
        if ru_addr.chapter_num == '16' and int(ru_addr.verse_num) > 8:
            return
        print 'Key Error: ' + str(e) + ', chapter=' + ru_addr.chapter_num + ', verse=' + str(ru_addr.verse_num) + ', address=' + str(ru_addr.addr_idx)

    def getAddressForReadingUnit(s, ru):
        ru_addr = s.base_addr
        for idx in range(s.slot_idx + 1, len(s.model['addresses'])):
            if ru.verse_num == ru_addr.verse_num and ru.addr_idx == ru_addr.addr_idx:
                break;

            ru_addr = s.model['addresses'][idx]

        return ru_addr

    def isC01Match(s, r_match, r_container):
        return False

    def isC05Match(s, r_match, r_container):
        return False

    def addBezaeCorrector(s):
        t_form = ''
        reading = s.var_unit.readings[0]
        if type(reading) is ReadingGroup:
            reading = reading.readings[0]

        c_id = s.overlay_id
        has_corrector = False
        for ru in reading.readingUnits:
            ru_addr = s.getAddressForReadingUnit(ru)
            c_text = s.v_lookup[ru_addr.verse_num][ru_addr.addr_idx]
            if c_text and c_text == 'OMIT': # corrector erased text
                has_corrector = True
                continue
            elif c_text: # corrector inserted text
                rs = re.search(ur'([\u0391-\u03A9\u03B1-\u03C9om\. ]+) \{([A-Za-z\/]{1,3})(\?{0,1})\}', c_text)
                if not rs:
                    rs = re.search(ur'([\u0391-\u03A9\u03B1-\u03C9om\. ]+) \-\> \{(pm)\}', c_text)
                if rs:
                    has_corrector = True
                    if t_form:
                        t_form = t_form + ' '
                    t_form = t_form + rs.group(1)
                    c_id = rs.group(2)
                else:
                    s.info('Unrecognized Bezan corrector pattern at', s.var_unit.label)
            else: # corrector left original text
                orig_text = ru_addr.getTextFormForMS('05')
                if orig_text and orig_text != 'om.':
                    if t_form:
                        t_form = t_form + ' '
                    t_form = t_form + orig_text

        if has_corrector and t_form:
            s.var_unit.bezae_correctors[c_id] = t_form

    def addSinaiCorrector(s):
        t_form = ''
        reading = s.var_unit.readings[0]
        if type(reading) is ReadingGroup:
            reading = reading.readings[0]

        has_corrector = False
        for ru in reading.readingUnits:
            ru_addr = s.getAddressForReadingUnit(ru)
            c_text = s.v_lookup[ru_addr.verse_num][ru_addr.addr_idx]
            if c_text and c_text == 'OMIT': # corrector erased text
                has_corrector = True
                continue
            elif c_text: # corrector inserted text
                has_corrector = True
                if t_form:
                    t_form = t_form + ' '
                t_form = t_form + c_text
            else: # corrector left original text
                orig_text = ru_addr.getTextFormForMS('01')
                if orig_text and orig_text != 'om.':
                    if t_form:
                        t_form = t_form + ' '
                    t_form = t_form + orig_text

        if has_corrector and t_form:
            s.var_unit.sinai_correctors[s.overlay_id] = t_form

    def isContinuousMatch(s, r_match, r_container):
        is_match = True
        is_deferable = False
        deferred_text = None
        o_reading = ''
        for ru in r_match.readingUnits:
            ru_addr = s.getAddressForReadingUnit(ru)
            try:
                o_text = s.v_lookup[ru.verse_num][ru.addr_idx]
                if len(o_reading) > 0 and o_text == '-':
                    o_text = 'om.' # handle long sparse matches where final '-' is interpreted as 'om.' by non-overlay MSS, see 14.70.25,39 where na28 == 03

                text = ru.text
                if text != 'om.':
                    deferred_text = None
                if deferred_text:
                    text = deferred_text
                alt_forms = ru_addr.getAltFormsForReadingUnit(text)

                if not o_text in alt_forms:
                    is_match = False # unless intervening overlay addrs == 'om.' and next overlay addr is match
                    is_deferable = False
                    if o_text == 'om.':
                        is_deferable = True
                        if not deferred_text: # not already deferring!
                            deferred_text = ru.text
                    else: # overlay non-empty, start over
                        deferred_text = None
                    if not is_match and not is_deferable:
                        break
                else: # overlay match, start over
                    is_match = True # reachable only when still matching
                    deferred_text = None
                    if o_text == 'om.' or o_text == '-':
                        continue
                    if len(o_reading) > 0:
                        o_reading = o_reading + ' '
                    o_reading = o_reading + o_text
            except KeyError as e:
                is_match = False
                s.handleKeyError(e, ru_addr)

        # only add unique matches
        if is_match and not s.overlay_id in r_container.manuscripts:
            r_container.manuscripts.append(s.overlay_id)

        return is_match

    def isSynopticMatch(s, r_match, r_container):
        is_match = True
        o_reading = ''
        o_book = ''
        o_chapter = ''
        o_verses = []
        o_words = []
        for ru in r_match.readingUnits:
            ru_addr = s.getAddressForReadingUnit(ru)
            try:
                o_unit = s.v_lookup[ru.verse_num][ru.addr_idx]
                rs_test = re.search(r'REF', o_unit)
                rs = re.search(ur'\{REF\:([0-9\.\-,]+);VAL\:([\u0391-\u03A9\u03B1-\u03C9 A-Za-z\.]+)\|\|([J-M])([0-9]{1,2})\.([0-9]{1,2})\.([0-9\-,]+)\}', o_unit)

                # flag unparsable REF's
                if rs_test and not rs:
                    s.info('Unparsed REF at chapter', ru.chapter_num, ', verse', str(ru.verse_num), ', index', str(ru.addr_idx))

                if rs:
                    if rs.group(1) == s.var_unit.label and rs.group(2) == r_match.getDisplayValue():
                        o_book = rs.group(3)
                        o_chapter = rs.group(4)
                        o_verses.append(rs.group(5))
                        o_words = rs.group(6)
                        o_reading = rs.group(2)
                        is_match = True
                        break
                    else:
                        is_match = False
                        break
                else:
                    rs = re.search(r'\{NA\}', o_unit)
                    if rs:
                        sp = SynopticParallel('{NA}', '', '', '', '')
                        r_container.synopticParallels.append(sp)
                        continue

                if o_unit == 'om.':
                    continue

                rs = re.search(ur'([\u0391-\u03A9\u03B1-\u03C9 ]+) \{([J-M])(\d{1,2})\.(\d{1,2})\.(\d{1,2})\}', o_unit)
                if not rs:
                    is_match = False
                    break

                o_text = rs.group(1).strip()
                if not o_book: o_book = rs.group(2)
                if not o_chapter: o_chapter = rs.group(3)
                o_verses.append(rs.group(4))
                o_words.append(rs.group(5))

                alt_forms = ru_addr.getAltFormsForReadingUnit(ru.text)
                if o_text in alt_forms:
                    is_match = True
                    if len(o_reading) > 0:
                        o_reading = o_reading + ' '
                    o_reading = o_reading + o_text
                else:
                    is_match = False
                    break
            except KeyError as e:
                is_match = False
                s.handleKeyError(e, ru_addr)

        if is_match and len(o_reading) > 0:
            sp = SynopticParallel(o_reading, o_book, o_chapter, o_verses, o_words)
            r_container.synopticParallels.append(sp)

        return is_match
