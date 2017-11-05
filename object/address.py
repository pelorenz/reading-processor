#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os

from object.addressSlot import *
from object.textForm import *
from object.textFormGroup import *
from object.textInstance import *

class  Address(AddressSlot):

    # static: max number of forms at any address
    max_forms = 0

    # static: max number of non-singular forms at any address
    max_non_sing = 0

    special_matches = {
      u'ις':   [ u'ιης', u'ιησους', u'iesus', u'ihs', u'his', u'ihc', u'is', u'hs', u'ic' ],
      u'ιης':  [ u'ις', u'ιησους', u'iesus', u'ihs', u'his', u'ihc', u'is', u'hs', u'ic' ],
      u'ιυ':   [ u'ιηυ', u'ιησυ', u'ιησου', u'iesu', u'ihu' ],
      u'ιηυ':  [ u'ιυ', u'ιησυ', u'ιησου', u'iesu', u'ihu' ],
      u'ιησυ': [ u'ιυ', u'ιηυ', u'ιησου', u'iesu', u'ihu' ],
      u'ιν':   [ u'ιην', u'ιησουν', u'iesum', u'ihm' ],
      u'ιην':  [ u'ιν', u'ιησουν', u'iesum', u'ihm' ],
      u'ιω':   [ u'ιωου', u'ιωαννου' ],
      u'ιωου': [ u'ιω', u'ιωαννου' ],
      u'υς':   [ u'υις', u'υιος', u'filius' ],
      u'υις':  [ u'υς', u'υιος', u'filius' ],
      u'υυ':   [ u'υιυ', u'υιου', u'filii', u'fili' ],
      u'υιυ':  [ u'υυ', u'υιου', u'filii', u'fili' ],
      u'υω':   [ u'υιω', u'filio' ],
      u'υν':   [ u'υιν', u'υιον', u'filium' ],
      u'υιν':  [ u'υν', u'υιον', u'filium' ],
      u'θς':   [ u'θεος', u'deus', u'ds' ],
      u'θυ':   [ u'θεου', u'di', u'dei' ],
      u'θω':   [ u'θεω', u'do', u'deo' ],
      u'θν':   [ u'θεον', u'deum', u'dm' ],
      u'κς':   [ u'κυριος', u'dominus', u'dms', u'dns', u'dmns', u'doms' ],
      u'κυ':   [ u'κυριου', u'domini', u'dmi', u'dni' ],
      u'κω':   [ u'κυριω', u'domino', u'dmo', u'dno' ],
      u'κν':   [ u'κυριον', u'dominum', u'dmn', u'dnm' ],
      u'κε':   [ u'κυριε', u'domine', u'dme', u'dne', u'dome' ],
      u'πνα':  [ u'πνευμα', u'spiritus', u'spiritum', u'sps', u'spm' ],
      u'πτς':  [ u'πνς', u'πνος', u'πνευματος', u'spiritus', u'sps' ],
      u'πνς':  [ u'πτς', u'πνος', u'πνευματος', u'spiritus', u'sps' ],
      u'πνος': [ u'πτς', u'πνς', u'πνευματος', u'spiritus', u'sps' ],
      u'πνι':  [ u'πνατι', u'πνευματι', u'spiritui', u'spo', u'spu' ],
      u'πνατι':[ u'πνι', u'πνευματι', u'spiritui', u'spo', u'spu' ],
      u'πνατων':[ u'πνματων', u'πνευματων' ],
      u'πνματων':[ u'πνατων', u'πνευματων' ],
      u'πντα': [ u'πνατα', u'πνευματα' ],
      u'πνατα':[ u'πντα', u'πνευματα' ],
      u'χς':   [ u'χρς', u'χρης', u'χριστος', u'christus', u'xps', u'xrs' ],
      u'χρς':  [ u'χς', u'χρης', u'χριστος', u'christus', u'xps', u'xrs' ],
      u'χρης': [ u'χς', u'χρς', u'χριστος', u'christus', u'xps', u'xrs' ],
      u'χυ':   [ u'χρυ', u'χρηυ', u'χριστου', u'christi', u'xpi', u'xri' ],
      u'χρυ':  [ u'χυ', u'χρηυ', u'χριστου', u'christi', u'xpi', u'xri' ],
      u'χρηυ': [ u'χυ', u'χρυ', u'χριστου', u'christi', u'xpi', u'xri' ],
      u'χω':   [ u'χωι', u'χρω', u'χριστω', u'christo', u'xpo', u'xro' ],
      u'χωι':  [ u'χω', u'χρω', u'χριστω', u'christo', u'xpo', u'xro' ],
      u'χρω':  [ u'χω', u'χωι', u'χριστω', u'christo', u'xpo', u'xro' ],
      u'χν':   [ u'χρν', u'χριστον', u'xpm', u'christum', u'xrm' ],
      u'χρν':  [ u'χν', u'χριστον', u'xpm', u'christum', u'xrm' ],
      u'πρ':   [ u'πηρ', u'πατηρ', u'pater' ],
      u'πηρ':  [ u'πρ', u'πατηρ', u'pater' ],
      u'πρς':  [ u'πατερος', u'patris' ],
      u'πρι':  [ u'πατερι', u'patri' ],
      u'πρα':  [ u'πατερα', u'patrem' ],
      u'πρες': [ u'πατερες', u'patres' ],
      u'πρων': [ u'πατερων', u'patrum' ],
      u'παρι': [ u'πατερι', u'patribus' ],
      u'πρας': [ u'πατερος', u'patres' ],
      u'ουνος':[ u'ουρανος' ],
      u'ουνου':[ u'ουρανου' ],
      u'ουνω': [ u'ουρανω' ],
      u'ουνον':[ u'ουρανον' ],
      u'ουνων':[ u'ουρανων' ],
      u'ουνοις':[ u'ουρανοις' ],
      u'ανς':  [ u'ανος', u'ανπος', u'ανθρωπος' ],
      u'ανος': [ u'ανς', u'ανπος', u'ανθρωπος' ],
      u'ανπος':[ u'ανς', u'ανος', u'ανθρωπος' ],
      u'ανου': [ u'ανπου', u'ανθρωπου' ],
      u'ανπου':[ u'ανου', u'ανθρωπου' ],
      u'ανω':  [ u'ανπω', u'ανθρωπω' ],
      u'ανπω': [ u'ανω', u'ανθρωπω' ],
      u'ανον': [ u'ανπν', u'ανπον', u'ανθρωπον' ],
      u'ανπν': [ u'ανον', u'ανπον', u'ανθρωπον' ],
      u'ανπον':[ u'ανον', u'ανπν', u'ανθρωπον' ],
      u'ανοι': [ u'ανποι', u'ανθρωποι' ],
      u'ανποι':[ u'ανοι', u'ανθρωποι' ],
      u'ανων': [ u'ανθρωπων' ],
      u'ανοις':[ u'ανποις', u'ανθρωποις'],
      u'ανποις':[ u'ανοις', u'ανθρωποις'],
      u'ανους':[ u'ανθρωπους' ],
      u'δαδ':  [ u'δαυιδ' ],
      u'ιηλ':  [ u'ισλ', u'ισρλ', u'ισραηλ' ],
      u'ισλ':  [ u'ιηλ', u'ισρλ', u'ισραηλ' ],
      u'ισρλ': [ u'ιηλ', u'ισλ', u'ισραηλ' ],
      u'ιημ':  [ u'ιλημ', u'ιηλμ', u'ιεσλμ', u'ιερουσαλημ' ],
      u'ιλημ': [ u'ιημ', u'ιηλμ', u'ιεσλμ', u'ιερουσαλημ' ],
      u'ιηλμ': [ u'ιημ', u'ιλημ', u'ιεσλμ', u'ιερουσαλημ' ],
      u'ιεσλμ':[ u'ιημ', u'ιλημ', u'ιηλμ', u'ιερουσαλημ' ],
      u'σωρ':  [ u'σηρ', u'σωτηρ' ],
      u'σηρ':  [ u'σωρ', u'σωτηρ' ],
      u'σωρι': [ u'σωτηροι' ],
      u'σρς':  [ u'σωρς', u'στρος', u'σωτηρος' ],
      u'σωρς': [ u'σρς', u'στρος', u'σωτηρος' ],
      u'στρος':[ u'σρς', u'σωρς', u'σωτηρος' ],
      u'σρου': [ u'στρου', u'σταυρου' ],
      u'στρου':[ u'σρου', u'σταυρου' ],
      u'στρν': [ u'στρον', u'σταυρον' ],
      u'στρον':[ u'στρν', u'σταυρον' ],
      u'μηρ':  [ u'μητηρ' ],
      u'μρς':  [ u'μητρος' ],
      u'μρι':  [ u'μητρι' ],
      u'μρα':  [ u'μητερα' ],
      u'μηρων':[ u'μητερων' ]
    }

    def cmpForms(s, f1, f2):
        bezaeKey = '20005'
        if not s.ms_text_forms.has_key(bezaeKey):
            bezaeKey = '5'

        if s.ms_text_forms[bezaeKey] == f1:
            return -1
        elif s.ms_text_forms[bezaeKey] == f2:
            return 1

        if len(f1.linked_mss) > len(f2.linked_mss):
            return -1
        elif len(f1.linked_mss) < len(f2.linked_mss):
            return 1
        else:
            return 0

    def __init__(s, t_idx, c_num, v_num, a_idx):
        super(Address, s).__init__(t_idx, c_num, v_num)

        # address position in verse
        s.addr_idx = a_idx

        # text for each MS at address
        s.text_instances = []

        # text forms for address by form
        # TODO: fix me! treated as dictionary by csvProcessor, thereafter as list
        s.text_forms = {}

        # text forms mapped to MS by id
        s.ms_text_forms = {}

        # reference text form
        s.reference_form = ''

        # text form objects sorted by occurrence
        s.sorted_text_forms = []

        # text form strings sorted by occurrence
        s.sorted_form_content = []

        # text form MSS sorted by occurrence
        s.sorted_attestations = []

        # variation units
        s.variation_units = []

    def jsonSerialize(s):
        return { 'addressIndex': s.addr_idx, 'chapter': s.chapter_num, 'verse': int(s.verse_num), 'tokenIndex': s.token_idx, '_type': 'address', 'textForms': s.sorted_text_forms, 'variationUnits': s.variation_units }

    def nonSingularTextForms(s):
        non_sing = []
        for frm in s.sorted_text_forms:
            if len(frm.linked_mss) > 1:
                non_sing.append(frm)
        return non_sing

    def getSortedContent(s, idx):
        if idx > len(s.sorted_form_content) - 1:
            return ''
        else:
            return s.sorted_form_content[idx]

    def getSortedAttestations(s, idx):
        if idx > len(s.sorted_attestations) - 1:
            return ''
        else:
            return ' '.join(s.sorted_attestations[idx])

    def getSortedLinkedMss(s, idx):
        if idx > len(s.sorted_attestations) - 1:
            return []
        else:
            return s.sorted_text_forms[idx].linked_mss

    def getTextFormForMS(s, ms):
        for tform in s.sorted_text_forms:
            if isinstance(tform, TextForm):
                if ms in tform.linked_mss:
                    return tform.form
            elif isinstance(tform, TextFormGroup):
                for m_list in tform.linked_mss:
                    if ms in m_list:
                        return tform.mainForm

        return ''

    def getAltFormsForReadingUnit(s, text):
        text_forms = []
        for tform in s.sorted_text_forms:
            if isinstance(tform, TextForm):
                if tform.getForm() == text:
                    text_forms.append(tform.getForm())
            elif isinstance(tform, TextFormGroup):
                maybe_forms = []
                is_match = False
                for sform in tform.textForms:
                    maybe_forms.append(sform.getForm())
                    if sform.getForm() == text:
                        is_match = True
                if is_match:
                    text_forms = maybe_forms
                    break

        if Address.special_matches.has_key(text):
            text_forms = list(set(text_forms) | set(Address.special_matches[text]))

        return text_forms

    def buildSortedItems(s):
        s.sorted_form_content = []
        s.sorted_attestations = []

        # sort forms and attestations in separate lists (for rendering)
        for frm in s.sorted_text_forms:
            s.sorted_form_content.append(frm.getForm())
            s.sorted_attestations.append(frm.linked_mss)

    def initializeTextForms(s, language):
        # populate all unique forms by comparing text instances
        for inst in s.text_instances:
            val = inst.content.lower()
            # IMPORTANT - uncomment for Mark 1!
            #if language == 'latin':
            #    val = val.replace(u'v', u'u')
            if not s.text_forms.has_key(val):
                form = TextForm(val, language, '', '', True)
                s.text_forms[val] = form
                s.sorted_text_forms.append(form)
            else:
                form = s.text_forms[val]

            form.linked_mss.append(inst.manuscript)
            s.ms_text_forms[inst.manuscript.id] = form

        # sort forms by attestation
        s.sorted_text_forms = sorted(s.sorted_text_forms, cmp=s.cmpForms)

        # sort forms and attestations in separate lists (for rendering)
        s.buildSortedItems()

        # track maximum of text forms held by any address in static variable
        num_forms = len(s.sorted_text_forms)
        if num_forms > Address.max_forms:
            Address.max_forms = num_forms

        # track maximum of non-singular text forms held by any address in static variable
        non_sing = len(s.nonSingularTextForms())
        if non_sing > Address.max_non_sing:
            Address.max_non_sing = non_sing

    def getMatchingForms(s, tokens):
        values = []
        for f_obj in s.sorted_text_forms:
            if type(f_obj) is TextFormGroup:
                g_vals = []
                is_match = False
                for frm in f_obj.textForms:
                    if frm.form and frm.form != '':
                        if frm.form in tokens:
                            is_match = True
                        g_vals.append(frm.form)
                if is_match:
                    values.extend(g_vals)
            else: # TextForm
                if f_obj.form and f_obj.form != '' and f_obj.form in tokens:
                    values.append(f_obj.form)

        return list(set(values))

    def getAllForms(s):
        values = []
        for f_obj in s.sorted_text_forms:
            if type(f_obj) is TextFormGroup:
                for frm in f_obj.textForms:
                    if frm.form and frm.form != '':
                        values.append(frm.form)
            else: # TextForm
                if f_obj.form and f_obj.form != '':
                    values.append(f_obj.form)

        return list(set(values))

    def getMatchingLemmas(s, tokens):
        lemmas = []
        for f_obj in s.sorted_text_forms:
            if type(f_obj) is TextFormGroup:
                g_frms = []
                is_match = False
                for frm in f_obj.textForms:
                    if frm.form and frm.form != '':
                        if frm.form in tokens:
                            is_match = True
                        g_frms.append(frm)
                if is_match:
                    for frm in g_frms:
                        lemmas.extend(frm.getLemmas())
            else: # TextForm
                if f_obj.form and f_obj.form != '' and f_obj.form in tokens:
                    lemmas.extend(f_obj.getLemmas())

        return list(set(lemmas))

    def getAllLemmas(s):
        lemmas = []
        for f_obj in s.sorted_text_forms:
            if type(f_obj) is TextFormGroup:
                for frm in f_obj.textForms:
                    if frm.form and frm.form != '':
                        lemmas.extend(frm.getLemmas())
            else: # TextForm
                if f_obj.form and f_obj.form != '':
                    lemmas.extend(f_obj.getLemmas())

        return list(set(lemmas))
