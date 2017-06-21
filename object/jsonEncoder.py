import sys, os, json

from object.address import *
from object.manuscript import *
from object.textForm import *
from object.verseDelimiter import *

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if (isinstance(obj, Address) or \
            isinstance(obj, Manuscript) or \
            isinstance(obj, TextForm) or \
            isinstance(obj, VerseDelimiter)):
            return obj.jsonSerialize()
        return json.JSONEncoder.default(self, obj)
