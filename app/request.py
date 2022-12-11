import requests
from settings import Settings
from utils import Logger


def process_url(url, headers, oneprovider=None):
    if "oneprovider/" in url:
        if oneprovider:
            # WIP
            url = "https://cesnet-oneprovider-01.datahub.egi.eu/api/v3/" + url, headers
        else:
            url = Settings.get().ONEPROVIDER_API_URL + url

        headers.update(Settings.get().ONEPROVIDER_AUTH_HEADERS)
    elif "onepanel/" in url:
        url = Settings.get().ONEPANEL_API_URL + url
        headers.update(Settings.get().ONEPANEL_AUTH_HEADERS)
    elif "onezone/" in url:
        url = Settings.get().ONEZONE_API_URL + url
        headers.update(Settings.get().ONEZONE_AUTH_HEADERS)
    else:
        Logger.log(1, "No comunication party in URL (%s)" % url)
        return None, None
    return url, headers


def response_print(response):
    if not response.ok:
        Logger.log(2, "Response isn't ok (response code = %s)" % response.status_code)


def debug_print(response):
    Logger.log(4, "Response: %s" % response)
    if response.ok and response.content != b"":
        Logger.log(5, "Response content:", pretty_print=response.json())
    elif not response.ok and response.content != b"":
        Logger.log(1, "Response content:", pretty_print=response.json())


def get(url, headers=dict()):
    url, headers = process_url(url, headers)
    response = requests.get(url, headers=headers)
    # commented because not ok is sometimes right response
    # timeout_counter = 3
    # while timeout_counter > 0:
    #     response = requests.get(url, headers=headers, verify=False)
    #     if response.ok:
    #         timeout_counter = 0
    #     else:
    #         if Settings.get().debug >= 1: print("Warning: request timeouted", str(4-timeout_counter), "ouf of 3 times")
    #         if Settings.get().debug >= 1: print("Warning: request url: ", url)
    #         timeout_counter = timeout_counter - 1
    #         time.sleep(10)
    response_print(response)
    debug_print(response)
    return response


def patch(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)
    response = requests.patch(url, headers=headers, data=data)
    response_print(response)
    debug_print(response)
    return response


def put(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)
    response = requests.put(url, headers=headers, data=data)
    response_print(response)
    debug_print(response)
    return response


def post(url, headers=dict(), data=dict(), oneprovider=None):
    url, headers = process_url(url, headers, oneprovider)
    response = requests.post(url, headers=headers, data=data)
    response_print(response)
    debug_print(response)
    return response


def delete(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)
    response = requests.delete(url, headers=headers, data=data)
    response_print(response)
    debug_print(response)
    return response
