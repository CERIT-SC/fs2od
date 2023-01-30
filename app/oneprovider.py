from settings import Settings
from utils import Logger
import request

def getConfiguration():
    Logger.log(4, "getConfiguration():")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_configuration
    url = "oneprovider/configuration"
    response = request.get(url)
    return response.json()
