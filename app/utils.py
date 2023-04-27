import re
import uuid
from datetime import datetime, timedelta
from pprint import pprint
from settings import Settings
from typing import List


class Utils:
    @staticmethod
    def clearOnedataName(name: str):
        """
        Clear given name (e.g. replace not allowed characters).
        """
        name = name.strip()
        name = name[0 : Settings.get().MAX_ONEDATA_NAME_LENGTH]
        name = name.replace("+", "_")
        name = name.replace("@", "_")
        name_list = name.split()
        name = "_".join(name_list)
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

    @staticmethod
    def is_time_for_action(previous_perform_time: datetime, time_until: datetime, intervals: List[timedelta],
                           response_on_weird_condition: bool = False):
        """
        Decides if an action should be performed based on previous perform time, time until another (often stronger)
        action is performed and intervals before time_until when action should be performed.
        Definition: State, when previous perform time is higher than actual time is here called weird condition.
        Weird conditions is not possible in reality; it can be caused only by misconfigured time or users intervention
        When weird condition is reached, function will return user defined value. This is because the stronger action
        can be so important, that any misconfiguration is cause to perform this weaker action.
        Intervals have to be sorted in reverse order, it will not be checked
        """
        now = datetime.now()
        if time_until < now:
            return False
        # impossible states in reality, can be caused by time misconfiguration
        # user may decide to perform an action on that state
        if previous_perform_time > now:
            return response_on_weird_condition
        for interval in intervals:
            date_to_be_executed = time_until - interval

            if (date_to_be_executed < now) ^ (date_to_be_executed < previous_perform_time):
                return True

        return False


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
