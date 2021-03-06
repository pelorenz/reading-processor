# -*- coding: utf-8 -*-
import os, json, re

from utility.config import *

class KMap:
    def casesForId(s, id, cases, refMap):
        ccnt = 0
        for case in cases:
            vars = refMap[case].split(', ')
            isMatch = True
            for idx, var in enumerate(vars):
                if var[:1] == '~': # neg var
                    if id[idx] != '0':
                        isMatch = False
                        break
                else: # pos var
                    if id[idx] != '1':
                        isMatch = False
                        break

            if isMatch:
                ccnt = ccnt + 1

        return ccnt

    def cellIdFromCode(s, row, col):
        id = ''
        l_id = row + col
        last_c = ''
        for i, c in enumerate(l_id):
            if last_c and last_c != u'̄':
                if c == u'̄':
                    id = id + '0'
                else:
                    id = id + '1'
            last_c = c

        if last_c != u'̄':
            id = id + '1'
            
        return 'c' + id

    def headIdFromCode(s, hdr):
        id = ''
        last_c = ''
        for i, c in enumerate(hdr):
            if last_c and last_c != u'̄':
                if c == u'̄':
                    id = id + '0'
                else:
                    id = id + '1'
            last_c = c

        if last_c != u'̄':
            id = id + '1'
            
        return id

    def colIdFromBits(s, bits, symbols):
        return bits[-len(symbols):]

    def rowIdFromBits(s, bits, symbols):
        return bits[:len(symbols)]

    def hasSymbol(s, symbol, codestr):
        return True if re.search(symbol, codestr) and not re.search(symbol + u'\u0304', codestr) else False

    def replaceDash(s, ids):
        n_ids = []
        for id in ids:
            pos = id.find('-')
            if pos != -1:
                id1 = id
                id2 = id
                id1 = id1.replace('-', '1', 1)
                id2 = id2.replace('-', '0', 1)
                n_ids.extend(s.replaceDash([id1, id2]))
            else:
                n_ids.append(id)
        return n_ids

    def exprToIds(s, exp):
        ids = [''.join(exp['vars'])]
        ids = s.replaceDash(ids)
        return ids

    def msFromCodemap(s, code, codemap):
        for cod, ms in codemap:
            if cod == code:
                return ms
        return ''