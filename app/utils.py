import re
import uuid
from datetime import datetime
from pprint import pprint
from settings import Settings


class Utils:
    @staticmethod
    def clearOnedataName(name):
        """
        Clear given name (e.g. replace not allowed characters).
        """
        name = name[0 : Settings.get().MAX_ONEDATA_NAME_LENGTH]
        name = name.replace("+", "_")
        name = name.replace("@", "_")
        return name

    @staticmethod
    def isValidOnedataName(name):
        """
        Onedata name must be 2-50 characters long and composed only of UTF-8 letters, digits, brackets and underscores.
        Dashes, spaces and dots are allowed (but not at the beginning or the end).
        """
        # test length and charaters in the name
        if Settings.get().MIN_ONEDATA_NAME_LENGTH <= len(
            name
        ) <= Settings.get().MAX_ONEDATA_NAME_LENGTH and re.match("^[a-zA-Z0-9()_\-.]*$", name):
            # test the first and the last character
            if re.match("^[a-zA-Z0-9()_]$", name[0]) and re.match("^[a-zA-Z0-9()_]$", name[-1]):
                return True

        return False

    @staticmethod
    def create_uuid(length):
        """
        Return random uuid with given length (up to 32 characters).
        """
        if length > 32:
            raise ValueError("Length must be max 32 chars")
        return uuid.uuid4().hex[:length]


class Logger:
    @staticmethod
    def log(level, message, space_id=None, pretty_print=None):
        """
        Print the message if the global verbose level is equal or greater then the given level.
        """
        if Settings.get().debug >= level:
            current_datetime = datetime.now()
            prefix = ""
            if level == 1:
                prefix = "error"
            elif level == 2:
                prefix = "warning"
            elif level == 3:
                prefix = "info"
            elif level == 4:
                prefix = "debug"
            elif level >= 5:
                prefix = "verbose"

            # log record parts are divided by single spaces, message (msg) have to be the last part
            if space_id:
                print("%s [%s] space=%s msg=%s" % (current_datetime, prefix, space_id, message))
            else:
                print("%s [%s] msg=%s" % (current_datetime, prefix, message))

            if pretty_print:
                pprint(pretty_print)
