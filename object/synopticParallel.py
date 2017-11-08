import sys, os

class  SynopticParallel(object):

    def __init__(s, text, book, chapter, verses, words):
        s.text = text
        s.book = book
        s.chapter = chapter
        s.verses = verses
        s.words = words # type(s.words) == list or type(s.words) == str

    def jsonSerialize(s):
        return { '_type': 'synopticParallel', 'text': s.text, 'book': s.book, 'chapter': s.chapter, 'verses': s.verses, 'words': s.words }

    def __str__(s):
        value = s.book + s.chapter
        if len(set(s.verses)) == 1: # single verse
            verse = s.verses[0]
            words = ''
            if type(s.words) == list:
                lastWord = None
                tokens = []
                for word in s.words:
                    if len(tokens) == 0:
                        tokens.append(word)
                    else:
                        if (int(word) - int(lastWord) == 1):
                            if tokens[-1] != '-':
                                tokens.append('-')
                        else:
                            if tokens[-1] == '-':
                                tokens.append(lastWord)
                            tokens.append(',')
                            tokens.append(word)
                    lastWord = word
                if tokens[-1] == ',' or tokens[-1] == '-':
                    tokens.append(lastWord)
                for idx, tok in enumerate(tokens):
                    if idx == 0:
                        words = tok
                    else:
                        words = words + tok
            else: # type(s.words) == str
                words = s.words
            value = value + '.' + verse + '.' + words
        else: # multiple verses
            words = ''
            for idx, verse in enumerate(s.verses):
                word = verse + '.' + s.words[idx]
                if len(words) > 0:
                    words = words + ','
                words = words + word
            value = value + '.' + words
        return value

    def getBook(s):
        if s.book == 'M':
            return 'Mt'
        elif s.book == 'K':
            return 'Mk'
        else:
            if s.book == 'L':
                return 'Lk'
            elif s.book == 'J':
                return 'Jn'
            else:
                return ''

    def getSummary(s):
        value = s.getBook() + u' ' + s.chapter
        if len(set(s.verses)) == 1: # single verse
            value = value + ':' + s.verses[0]
        else: # multiple verses
            value = ''
            for verse in s.verses:
                if len(value) > 0:
                    value = value + u', '
                value = value + verse
        return value
