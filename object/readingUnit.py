#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, collections, json

from object.addressSlot import *

class  ReadingUnit(AddressSlot):

    def __init__(s, t_idx, v_num, a_idx, txt):
        super(ReadingUnit, s).__init__(t_idx, v_num)

        # address position in verse
        s.addr_idx = a_idx

        # text value
        s.text = txt

    def jsonSerialize(s):
        return { 'addressIndex': s.addr_idx, 'verse': int(s.verse_num), 'tokenIndex': s.token_idx, '_type': 'readingUnit', 'text': s.text }
