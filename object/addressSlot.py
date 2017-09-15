import sys, os

class  AddressSlot(object):

    def __init__(self, t_idx, c_num, v_num):
        # address slot position in chapter tokens
        self.token_idx = t_idx

        # biblical chapter number
        self.chapter_num = c_num

        # biblical verse number
        self.verse_num = v_num
