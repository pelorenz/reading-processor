import sys, os, json

from object.address import *
from object.manuscript import *
from object.reading import *
from object.readingGroup import *
from object.readingUnit import *
from object.synopticParallel import *
from object.textForm import *
from object.textFormGroup import *
from object.variationUnit import *
from object.verseDelimiter import *

class ComplexDecoder(json.JSONDecoder):
    def __init__(s, *args, **kwargs):
        json.JSONDecoder.__init__(s, object_hook=s.object_hook, *args, **kwargs)

    def info(s, *args):
        info = ''
        for i, arg in enumerate(args):
            if i > 0: info += ' '
            info += str(arg).strip()
        print(info)

    def object_hook(s, obj):
        if '_type' not in obj:
            return obj
        type = obj['_type']
        if type == 'base':
            return { 'addresses': obj['addresses'], 'max_forms': obj['maxFormsAtAddress'], 'max_non_sing': obj['maxNonSingularFormsAtAddress']}
        if type == 'address':
            address = Address(obj['tokenIndex'], obj['chapter'], obj['verse'], obj['addressIndex'])
            address.sorted_text_forms = obj['textForms']
            if obj.has_key('variationUnits'):
                address.variation_units = obj['variationUnits']
            address.buildSortedItems()
            return address
        if type == 'reading':
            reading = Reading(obj['displayValue'])
            reading.manuscripts = obj['manuscripts']
            reading.readingUnits = obj['readingUnits']
            try:
                reading.synopticParallels = obj['synopticParallels']
            except KeyError as e:
                action = None
            return reading
        if type == 'readingGroup':
            reading_group = ReadingGroup(obj['displayValue'])
            reading_group.readings = obj['readings']
            reading_group.manuscripts = obj['manuscripts']
            try:
                reading_group.synopticParallels = obj['synopticParallels']
            except KeyError as e:
                action = None
            return reading_group
        if type == 'readingUnit':
            reading_unit = ReadingUnit(obj['tokenIndex'], obj['chapter'], obj['verse'], obj['addressIndex'], obj['text'])
            return reading_unit
        if type == 'synopticParallel':
            return SynopticParallel(obj['text'], obj['book'], obj['chapter'], obj['verses'], obj['words'])
        if type == 'textForm':
            morph = ''
            if obj.has_key('morph'): lang = obj['morph']

            lemma = ''
            if obj.has_key('lemma'): lemma = obj['lemma']

            text_form = TextForm(obj['form'], obj['language'], morph, lemma, False)
            text_form.linked_mss = obj['linkedManuscripts']
            return text_form
        if type == 'textFormGroup':
            text_form_group = TextFormGroup(obj['mainForm'])
            text_form_group.textForms = obj['textForms']
            text_form_group.initMSS()
            return text_form_group
        if type == 'variationUnit':
            variation_unit = VariationUnit(obj['label'], obj['hasRetroversion'])
            variation_unit.readings = obj['readings']
            return variation_unit
        if type == 'verse':
            return VerseDelimiter(obj['tokenIndex'], '0', str(obj['verse']))
        return obj

class SegmentDecoder(json.JSONDecoder):
    def __init__(s, *args, **kwargs):
        json.JSONDecoder.__init__(s, object_hook=s.object_hook, *args, **kwargs)

    def object_hook(s, obj):
        if '_type' not in obj:
            return obj
        type = obj['_type']
