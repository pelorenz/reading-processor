import sys, os

class  TextInstance(object):

    def __init__(self, tok_idx, v_num, a_idx, ms, t_val):
        # address index
        self.addr_idx = a_idx

        # reference to manuscript of cited text
        self.manuscript = ms

        # cited text of specified MS at address
        self.content = t_val

        # index in entire CSV
        self.token_idx = tok_idx

        # verse number to which instance belongs
        self.verse_num = v_num
