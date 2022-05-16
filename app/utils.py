from pprint import pprint
from settings import Settings

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
