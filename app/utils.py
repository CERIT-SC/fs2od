from settings import Settings

class Logger():

    @staticmethod
    def log(level, message):
        prefix = ""
        if level == 1: 
            prefix = "INFO"
        elif level == 2: 
            prefix = "DEBUG"
        elif level == 3: 
            prefix = "ERROR"
        else: 
            prefix = ""
        prefix = "["+prefix+"]"

        if Settings.get().debug >= level:
            print(prefix, message)
