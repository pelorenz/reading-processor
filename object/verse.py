import sys, os

from object.addressSlot import *

class  Verse (AddressSlot):

    def __init__(self, t_idx, v_num):
        super(Verse, self).__init__(False, t_idx, v_num)

        # addresses assigned to verse
        self.addresses = []

    def addAddress(self, addr):
        s = self
        s.addresses.append(addr)
