import sys, os, json

class  Config:
    def __init__(self, configFile):
        stream = None
        try:
            stream = open(configFile, 'r')
            self.configFile = json.load(stream)
        except:
            print('EXCEPTION: There was a problem opening the config file', configFile)
            print('The default config filename is processor-config.json. The default path is the script directory.')
            print ('')
            raise
        finally:
            if stream is not None:
                stream.close()

    # Accessors
    def get(self, key):
        if (key in self.configFile):
            return self.configFile[key]
        else:
            return None

    def getDefault(self, key, default):
        if (key in self.configFile):
            return self.configFile[key]
        else:
            return default
