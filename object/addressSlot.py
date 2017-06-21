import sys, os

class  AddressSlot(object):

    def __init__(self, t_idx, v_num):
        # address slot position in chapter tokens
        self.token_idx = t_idx

        # biblical verse number
        self.verse_num = v_num
