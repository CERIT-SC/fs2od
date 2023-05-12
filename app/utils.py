import re
import urllib.parse
import uuid
from datetime import datetime, timedelta
from pprint import pprint
from urllib.parse import urlparse

from settings import Settings
from typing import List, Union


def _convert_to_urlparse_result(url: str) -> Union[urllib.parse.ParseResult, bool]:
    """
    Returns ParseResult object from URL
    If any of the URL cannot be converted to urllib object (ParseResult), returns False
    """
    Logger.log(4, f"_convert_to_urlparse_result(url={url})")
    # if url does not have // in it, it is considered as a path and netloc is not interpreted
    if "//" not in url:
        url = "//" + url

    try:
        url_object = urlparse(url)
    except ValueError as e:
        Logger.log(3, f"URL cannot be parsed. Error while processing, error: {e}")
        return False

    return url_object


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
                           response_on_weird_condition: bool = False) -> bool:
        """
        Decides if an action should be performed based on previous perform time, time until another (often stronger)
        action is performed and intervals before time_until when action should be performed.
        Definition: State, when previous perform time is higher than actual time is here called weird condition.
        Weird conditions is not possible in reality; it can be caused only by misconfigured time or users intervention
        When weird condition is reached, function will return user defined value. This is because the stronger action
        can be so important, that any misconfiguration is cause to perform this weaker action.
        Intervals have to be sorted in reverse order, it will not be checked
        """
        Logger.log(4, f"is_time_for_action(previous={previous_perform_time.isoformat()}, "
                      f"until={time_until.isoformat()}, "
                      f"intervals={[str(interval.days) + 'd' + str(interval.seconds) + 's' for interval in intervals]})")
        now = datetime.now()
        if time_until < now:
            return False
        # impossible states in reality, can be caused by time misconfiguration
        # user may decide to perform an action on that state
        if previous_perform_time > now:
            return response_on_weird_condition
        for interval in intervals:
            date_to_be_executed = time_until - interval

            if (date_to_be_executed <= now) ^ (date_to_be_executed <= previous_perform_time):
                return True

        return False

    @staticmethod
    def is_domain_name_the_same(url_1: str, url_2: str) -> bool:
        """
        Decides if domain name is the same.
        Returns True when domain names are the same, otherwise false
        If any of the URL cannot be converted to urllib object (ParseResult), returns False
        >>> Utils.is_domain_name_the_same("google.com", "https://google.com/page/page2?query=r#fragment1")  # True
        >>> Utils.is_domain_name_the_same("auth.google.com", "https://google.com/page/page2?query=r#fragment1")  # True
        >>> Utils.is_domain_name_the_same("gogle.com", "https://google.com/page/page2?query=r#fragment1")  # False
        """
        Logger.log(4, f"is_domain_name_the_same(url1={url_1},url2={url_2})")

        url1_object = _convert_to_urlparse_result(url_1)
        url2_object = _convert_to_urlparse_result(url_2)

        netloc1_split = url1_object.netloc.split(".")
        netloc2_split = url2_object.netloc.split(".")

        # if there is domain name and top level domain
        return netloc1_split[-2:] == netloc2_split[-2:]

    @staticmethod
    def is_host_name_the_same(url_1: str, url_2: str) -> bool:
        """
        Decides if host name is the same.
        Returns True when host names are the same, otherwise false
        If any of the URL cannot be converted to urllib object (ParseResult), returns False
        >>> Utils.is_domain_name_the_same("google.com", "https://google.com/page/page2?query=r#fragment1")  # True
        >>> Utils.is_domain_name_the_same("auth.google.com", "https://google.com/page/page2?query=r#fragment1")  # False
        >>> Utils.is_domain_name_the_same("gogle.com", "https://google.com/page/page2?query=r#fragment1")  # False
        """
        Logger.log(4, f"is_host_name_the_same(url1={url_1},url2={url_2})")

        url1_object = _convert_to_urlparse_result(url_1)
        url2_object = _convert_to_urlparse_result(url_2)

        return url1_object.netloc == url2_object.netloc


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
