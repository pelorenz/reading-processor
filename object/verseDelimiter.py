import sys, os

from object.addressSlot import *

class  VerseDelimiter(AddressSlot):
    def __init__(s, t_idx, c_num, v_num):
        super(VerseDelimiter, s).__init__(t_idx, c_num, v_num)

    def jsonSerialize(s):
        return { 'verse': int(s.verse_num), 'tokIdx': s.token_idx, '_type': 'verse' }