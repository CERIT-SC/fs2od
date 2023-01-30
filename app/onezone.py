from settings import Settings
from utils import Logger
import request

def getConfiguration():
    Logger.log(4, "getConfiguration():")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_configuration
    url = "onezone/configuration"
    response = request.get(url)
    return response.json()


def getCurrentUserDetails():
    Logger.log(4, "getCurrentUserDetails():")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_current_user
    url = "onezone/user"
    response = request.get(url)
    if not response.ok:
        Logger.log(1, "Current user details can't be retrieved")

    return response.json()
