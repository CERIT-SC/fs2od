import re
from pprint import pprint
from settings import Settings

class Utils():
    @staticmethod
    def clearOnedataName(name):
        """
        Clear given name (e.g. replace not allowed characters).
        """
        name = name[0:Settings.get().MAX_ONEDATA_NAME_LENGTH]
        name = name.replace("+", "_")
        return name

    # not used
    @staticmethod
    def isValidOnedataName(name):
        """
        Onedata name must be 2-50 characters long and composed only of UTF-8 letters, digits, brackets and underscores. 
        Dashes, spaces and dots are allowed (but not at the beginning or the end).
        """
        # test length and charaters in the name
        if Settings.get().MIN_ONEDATA_NAME_LENGTH <= len(name) <= Settings.get().MAX_ONEDATA_NAME_LENGTH and re.match('^[a-zA-Z0-9()_\-.]*$', name):
            # test the first and the last character
            if re.match('^[a-zA-Z0-9()_]$', name[0]) and re.match('^[a-zA-Z0-9()_]$', name[-1]):
                return True

        return False


class Logger():

    @staticmethod
    def log(level, message, pretty_print=None):
        """
        Print the message if the global verbose level is equal or greater then the given level.
        """
        if Settings.get().debug >= level:
            prefix = ""
            if level == 1: 
                prefix = "Error"
            elif level == 2: 
                prefix = "Warning"
            elif level == 3: 
                prefix = "Info"
            elif level == 4:
                prefix = "Debug"
            elif level >= 5:
                prefix = "Verbose"

            prefix = "[" + prefix + "]"
            print(prefix, message)

            if pretty_print:
                pprint(pretty_print)
