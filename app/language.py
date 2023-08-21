import os

from settings import Settings
from utils import Logger


def get_filename_by_localization(filename: str) -> str:
    """
    Returns file name extended with localization. If localized file does not exist, returns given file.
    If given file does not exist, returns it with error in log
    """
    Logger.log(4, f"get_filename_by_localization(filename={filename})")

    if not os.path.exists(filename):
        Logger.log(1, f"File with name {filename} does not exist, returning with possibility of crashing the program.")
        return filename

    language_extension = Settings.get().MESSAGING.email.language  # nothing if default, .ex when other
    filename_list = filename.split(".")

    if len(filename_list) == 1:
        filename_list[0] += language_extension
        return filename_list[0]

    filename_list[-2] += language_extension

    new_filename = ".".join(filename_list)
    if os.path.exists(new_filename):
        return new_filename

    Logger.log(5, f"Using filename {filename}.")
    return filename
