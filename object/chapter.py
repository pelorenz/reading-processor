import sys, os

class  Chapter(object):

    def __init__(self, ch_num):
        self.chapter_num = ch_num

        # biblical chapter number
        self.chapter_num = None

        # verses assigned to chapter
        self.verses = []

    def addVerse(self, v):
        s = self
        s.verses.append(v)
