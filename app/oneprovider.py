from utils import Logger
import request


def get_configuration(index: int = 0) -> dict:
    """
    Returns configuration for Oneprovider with given index.
    On success returns dict with information
    Otherwise returns empty dict
    """
    Logger.log(4, f"get_configuration(order={index}):")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_configuration
    url = "oneprovider/configuration"
    response = request.get(url, oneprovider_index=index)
    if response.ok:
        return response.json()
    else:
        return {}


def get_provider_id(index: int = 0) -> str:
    """
    Returns provider id for Oneprovider with given index.
    On success returns string with provider id
    Otherwise returns empty string
    """
    Logger.log(4, f"get_provider_id(order={index}):")
    conf = get_configuration(index)
    if not conf:
        return ""
    return conf["providerId"]
