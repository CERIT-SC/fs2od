from settings import Settings
from utils import Logger
import request


def getConfiguration(order: int = 0):
    Logger.log(4, f"getConfiguration(order={order}):")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_configuration
    url = "oneprovider/configuration" + f"[{order}]"
    response = request.get(url)
    return response.json()
