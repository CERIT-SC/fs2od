from settings import Settings
from utils import Logger
import request


def getConfiguration(index: int = 0):
    Logger.log(4, f"getConfiguration(order={index}):")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_configuration
    url = "oneprovider/configuration"
    response = request.get(url, oneprovider_index=index)
    return response.json()
