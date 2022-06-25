import os
import sys
from pprint import pprint
import ruamel.yaml

class Settings():
    """
    Singleton class to serve the global configuration.
    """
    __instance = None
    config=None

    def __init__(self, config):
        """
        Virtually private constructor.
        """
        if Settings.__instance != None:
            raise Exception("This class is a singleton! Created once, otherwise use Settings.get_instance()")
        else:
            self.setup(config)
            Settings.__instance = self

    @staticmethod
    def get():
        """
        Static access method, return instance of Settings or instantiate it. 
        """
        if Settings.__instance == None:
            Settings()
        return Settings.__instance

    def setup(self, config_file):
        """
        Load configuration from given YAML file.
        """ 
        if os.path.exists(config_file):
            with open(config_file, 'r') as stream:
                try:
                    yaml = ruamel.yaml.YAML(typ='safe')
                    self.config = yaml.load(stream)
                except Exception as e:
                    print("Error: exception occured during loading config file", config_file)
                    print(str(e))
                    sys.exit(1)
                
                self.debug = self.config["verboseLevel"]

                self.TEST = self.config['testMode']
                self.TEST_PREFIX = self.config['testModePrefix']

                # Setup the access Onedata variables
                self.ONEZONE_HOST = self.config['onezone']['host']
                self.ONEZONE_API_KEY = self.config['onezone']['apiToken']

                self.ONEPROVIDER_HOST = self.config['oneprovider']['host']
                self.ONEPROVIDER_API_KEY = self.config['oneprovider']['apiToken']

                self.ONEPANEL_HOST = self.config['onepanel']['host']
                self.ONEPANEL_API_KEY = self.config['onepanel']['apiToken']

                self.ONEZONE_API_URL = self.ONEZONE_HOST + "/api/v3/"
                self.ONEPROVIDER_API_URL = self.ONEPROVIDER_HOST + "/api/v3/"
                self.ONEPANEL_API_URL = self.ONEPANEL_HOST + "/api/v3/"

                self.ONEZONE_AUTH_HEADERS = {'x-auth-token' : self.ONEZONE_API_KEY}
                self.ONEPROVIDER_AUTH_HEADERS = {'x-auth-token' : self.ONEPROVIDER_API_KEY}
                self.ONEPANEL_AUTH_HEADERS = {'x-auth-token' : self.ONEPANEL_API_KEY}
                
                # Onedata name must be 2-50 characters long
                self.MIN_ONEDATA_NAME_LENGTH = 2
                self.MAX_ONEDATA_NAME_LENGTH = 50
        else:
            print("Error: config file %s doesn't exists" % config_file)
            sys.exit(1)
