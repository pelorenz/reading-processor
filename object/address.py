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
