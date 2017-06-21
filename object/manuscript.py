import sys, os, re

class  Manuscript(object):

    def __init__(s, id, language):
        # GA identifier of manuscript
        s.id = id

        # Display ID of manuscript
        if id.find('1') == 0:
            id = re.sub(r'^1000', 'P', id)
            id = re.sub(r'^100', 'P', id)
        elif id.find('2') == 0:
            id = re.sub(r'^2000', '0', id)
            id = re.sub(r'^200', '0', id)
            id = re.sub(r'^20', '0', id)
        else:
            id = re.sub(r'^3000', '', id)
            id = re.sub(r'^300', '', id)
            id = re.sub(r'^30', '', id)
            if len(id) == 5:
                id = re.sub(r'^3', '', id)

        if (language == 'latin' and id.isdigit()):
            id = 'VL' + id
        s.displayId = id
        s.language = language

    def jsonSerialize(s):
        return s.displayId