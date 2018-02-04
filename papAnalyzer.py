#! python2.7
# -*- coding: utf-8 -*-

import sys, os, string, re
from collections import OrderedDict
from object.util import *
from utility.config import *
from utility.options import *

class PapAnalyzer:

    LDAB_FIELD_MAP = {
        "TM nr": "tm_nr",
        "Catalogues": "catalogs",
        "Publication": "publication",
        "Other publications": "other_publications",
        "Authorname": "authorname",
        "Book": "book",
        "Quotations": "quotations",
        "Attested Authors": "attested_authors",
        "Provenance": "provenance",
        "Inventory": "inventory",
        "Century": "century",
        "Date": "date",
        "Material": "material",
        "Bookform": "bookform",
        "Recto-verso": "recto-verso",
        "Back": "back",
        "Reuse": "reuse",
        "Columns": "columns",
        "Language/script": "language",
        "Script_type": "script_type",
        "Culture": "culture",
        "Genre": "genre",
        "Religion": "religion",
        "Bibliography": "bibliography",
        "Stud Paleo Gr": "stud_paleo_gr",
        "Stud Literature": "stud_literature",
        "Photo": "photo",
        "URL": "url",
        "Note": "note"
    }

    STATE_HDRS = 'headers'
    LDAB_FIELD_STATES = {
        "Catalogues": "catalogs",
        "Publication": "publication",
        "Other publications": "other_publications",
        "Reuse": "reuse"
    }

    MPACK_FIELD_SEQUENCE = {
        0: "mpack_nr",
        1: "mp_former_ids",
        2: "mp_description",
        3: "mp_inventory_label",
        4: "mp_numbers",
        5: "mp_editions",
        6: "mp_dating",
        7: "mp_script_type"
    }

    MPACK_FIELD_MAP = {
        "Bibl.": "mp_bibliography",
        "Reprod.": "mp_repro"
    }

    def __init__(s):
        s.config = None
        s.options = None

        s.papyri = []

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def initPapyrus(s):
        papyrus = {}
        papyrus['headers'] = []
        papyrus['tm_nr'] = ''
        papyrus['pack_nr'] = ''
        papyrus['catalogs'] = []
        papyrus['publication'] = []
        papyrus['other_publications'] = []
        papyrus['authorname'] = ''
        papyrus['book'] = ''
        papyrus['quotations'] = ''
        papyrus['attested_authors'] = ''
        papyrus['provenance'] = ''
        papyrus['inventory'] = ''
        papyrus['century'] = ''
        papyrus['date'] = ''
        papyrus['material'] = ''
        papyrus['bookform'] = ''
        papyrus['recto-verso'] = ''
        papyrus['back'] = ''
        papyrus['reuse'] = []
        papyrus['columns'] = ''
        papyrus['language'] = ''
        papyrus['script_type'] = ''
        papyrus['culture'] = ''
        papyrus['genre'] = ''
        papyrus['religion'] = ''
        papyrus['bibliography'] = ''
        papyrus['stud_paleo_gr'] = ''
        papyrus['stud_literature'] = ''
        papyrus['photo'] = ''
        papyrus['url'] = ''
        papyrus['note'] = ''

        papyrus['mpack_nr'] = ''
        papyrus['mp_former_ids'] = ''
        papyrus['mp_description'] = ''
        papyrus['mp_inventory_label'] = ''
        papyrus['mp_numbers'] = []
        papyrus['mp_editions'] = ''
        papyrus['mp_dating'] = ''
        papyrus['mp_script_type'] = ''
        papyrus['mp_notes'] = []
        papyrus['mp_bibliography'] = ''
        papyrus['mp_repro'] = ''
        return papyrus

    def ldabRow(s, row, papyrus, ldab_state):
        parts = row.split(':')
        if len(parts) == 2:
            field = parts[0].strip()
            value = parts[1].strip()
            value = re.sub(r'\s+', ' ', value)
            if not field:
                if ldab_state == 'reuse':
                    if value:
                        papyrus['reuse'].append(value)
                    return 'reuse'
                return None

            if field == 'Catalogues':
                rs = re.search(r'Mertens\-Pack ([0-9\.]{1,10})', value)
                if rs:
                    papyrus['pack_nr'] = rs.group(1)

            if PapAnalyzer.LDAB_FIELD_MAP.has_key(field):
                if type(papyrus[PapAnalyzer.LDAB_FIELD_MAP[field]]) is list:
                    papyrus[PapAnalyzer.LDAB_FIELD_MAP[field]].append(value)
                else:
                    papyrus[PapAnalyzer.LDAB_FIELD_MAP[field]] = value

                if PapAnalyzer.LDAB_FIELD_STATES.has_key(field):
                    return PapAnalyzer.LDAB_FIELD_STATES[field]
                return None

            return None

        if ldab_state:
            if ldab_state == 'headers':
                parts = row.split('=')
                if len(parts) == 2:
                    row = parts[1].strip()
            papyrus[ldab_state].append(row)
        return ldab_state

    def mpackIndex(s, papyrus, mpack_idx, row):
        if PapAnalyzer.MPACK_FIELD_SEQUENCE.has_key(mpack_idx):
            papyrus[PapAnalyzer.MPACK_FIELD_SEQUENCE[mpack_idx]] = row

    def mpackField(s, papyrus, field, value):
        if PapAnalyzer.MPACK_FIELD_MAP.has_key(field):
            papyrus[PapAnalyzer.MPACK_FIELD_MAP[field]] = value

    def mpackRow(s, row, papyrus, mpack_idx):
        if mpack_idx >= len(PapAnalyzer.MPACK_FIELD_SEQUENCE):
            parts = row.split(':')
            if len(parts) == 2:
                field = parts[0]
                value = parts[1].strip()
                value = re.sub(r'\s+', ' ', value)
                s.mpackField(papyrus, field, value)
        else:
            value = re.sub(r'\s+', ' ', row).strip()
            s.mpackIndex(papyrus, mpack_idx, value)

    def main(s, argv):
        o = s.options = CommandLine(argv).getOptions()
        c = s.config = Config(o.config)

        MODE_LDAB = 'LDAB'
        MODE_MPACK = 'MPACK'

        infile_name = ''
        infile = None
        cachefile = None
        if o.file:
            infile_name = o.file
            infile = c.get('papyrusFolder') + infile_name + '.txt'
        else:
            s.info('Please specify input file with -f [filename]')
            return

        txtdata = ''
        with open(infile, 'r') as file:
            s.info('reading', infile)
            txtdata = file.read()
            file.close()

        mode = ''
        cur_papyrus = None
        ldab_state = None
        mpack_idx = 0
        rows = txtdata.split('\n')
        for rdx, row in enumerate(rows):
            if not row:
                if mode == MODE_MPACK:
                    mpack_idx = mpack_idx + 1
                continue

            if row == MODE_LDAB:
                mode = MODE_LDAB
                ldab_state = PapAnalyzer.STATE_HDRS
                if cur_papyrus:
                    s.papyri.append(cur_papyrus)
                cur_papyrus = s.initPapyrus()
                continue
            elif row == MODE_MPACK:
                mode = MODE_MPACK
                mpack_idx = 0
                continue

            if mode == MODE_LDAB:
                ldab_state = s.ldabRow(row, cur_papyrus, ldab_state)
            elif mode == MODE_MPACK:
                s.mpackRow(row, cur_papyrus, mpack_idx)
                mpack_idx = mpack_idx + 1

        if cur_papyrus: # last time
            s.papyri.append(cur_papyrus)

        result_file = c.get('papyrusFolder') + infile_name + '-output.csv'
        file = open(result_file, 'w+')
        h_str = 'Pack\tDescription\tInventory Label\tHeaders\tCatalogs\tAuthor\tBook\tProvenance\tInventory Details\tCentury\tDate\tMaterial\tBook Form\tRecto-Verso\tBack\tColumns\tLanguage\tScript Type\tCulture\tGenre\tReligion\tNote\tPublication\tOther Publications\tBibliography (1)\tPaleographical Studies\tLiterature\tPhoto\tURL\tEditions\tDating\tNotes\tBibliography (2)\tReproductions\tFormer IDs\n'
        file.write(h_str)
        for papyrus in s.papyri:
            p_str = ''

            p_str = p_str + papyrus['pack_nr']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['mp_description']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['mp_inventory_label']
            p_str = p_str + '\t'

            p_str = p_str + s.genMultiStr(papyrus, 'headers')
            p_str = p_str + '\t'

            p_str = p_str + s.genMultiStr(papyrus, 'catalogs')
            p_str = p_str + '\t'

            p_str = p_str + papyrus['authorname']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['book']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['provenance']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['inventory']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['century']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['date']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['material']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['bookform']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['recto-verso']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['back']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['columns']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['language']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['script_type']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['culture']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['genre']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['religion']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['note']
            p_str = p_str + '\t'

            p_str = p_str + s.genMultiStr(papyrus, 'publication')
            p_str = p_str + '\t'

            p_str = p_str + s.genMultiStr(papyrus, 'other_publications')
            p_str = p_str + '\t'

            p_str = p_str + papyrus['bibliography']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['stud_paleo_gr']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['stud_literature']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['photo']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['url']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['mp_editions']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['mp_dating']
            p_str = p_str + '\t'

            p_str = p_str + s.genMultiStr(papyrus, 'mp_notes')
            p_str = p_str + '\t'

            p_str = p_str + papyrus['mp_bibliography']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['mp_repro']
            p_str = p_str + '\t'

            p_str = p_str + papyrus['mp_former_ids']
            p_str = p_str + '\n'
            file.write(p_str)
        file.close()

    def genMultiStr(s, papyrus, field):
        m_str = ''
        for item in papyrus[field]:
            if m_str:
                m_str = m_str + '; '
            m_str = m_str + item
        return m_str

# Produce papyri CSVs
# papAnalyzer.py -v -f literary
PapAnalyzer().main(sys.argv[1:])
