import sys, os, json

from object.address import *
from object.manuscript import *
from object.reading import *
from object.readingGroup import *
from object.readingUnit import *
from object.textForm import *
from object.textFormGroup import *
from object.variationUnit import *
from object.verseDelimiter import *

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if (isinstance(obj, Address) or \
            isinstance(obj, Manuscript) or \
            isinstance(obj, Reading) or \
            isinstance(obj, ReadingGroup) or \
            isinstance(obj, ReadingUnit) or \
            isinstance(obj, TextForm) or \
            isinstance(obj, TextFormGroup) or \
            isinstance(obj, VariationUnit) or \
            isinstance(obj, VerseDelimiter)):
            return obj.jsonSerialize()
        return json.JSONEncoder.default(self, obj)
