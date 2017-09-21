import sys, argparse

from collections import namedtuple

class  CommandLine:
    def __init__(self, argv):
        self.argv = argv
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-c', '--config', help='Configuration filename with optional path. The config file must be placed in the script directory if a path is not provided. [processor-config.json]', default='processor-config.json')
        self.parser.add_argument('-f', '--file', help='Base file name for CSV and JSON input.')
        self.parser.add_argument('-a', '--range', help='Range identifier to specify range of variants for processing.')
        self.parser.add_argument('-C', '--chapter', help='Chapter name for variant diffs and other chapter-specific input.')
        self.parser.add_argument('-R', '--refMSS', help='Comma-delimited list of reference manuscripts.')
        self.parser.add_argument('-q', '--qcaSet', help='Set of QCA aggregates to apply.', default='default')
        self.parser.add_argument('-v', '--verbose', help='Display verbose output', action='store_true')
        self.parser.add_argument('-s', '--silent', help='Prevent output', action='store_true')
        self.parser.add_argument('-S', '--statsdir', help='Folder for stats output (TTMinimizer).')
        self.parser.add_argument('-H', '--hauptliste', help='Generate Hauptliste results for segments (dicer).', action='store_true')
        self.parser.add_argument('-Q', '--qca', help='Generate QCA results for segments (dicer).', action='store_true')
        self.parser.add_argument('-O', '--offsets', help='Generate offsets for segments (dicer).', action='store_true')
        self.parser.add_argument('-G', '--segmentConfig', help='Configuration of segment divisions.', default='default')

    def getOptions(self):
        dict = vars(self.parser.parse_args())
        options = namedtuple('Struct', dict.keys())(*dict.values())
        return options
