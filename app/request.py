import requests
from settings import Settings
from utils import Logger


def process_url(url: str, headers, oneprovider=None):
    order = 0
    if "oneprovider/" in url or "onepanel/" in url:
        # url of Oneprovider and Onepanel should be the same
        if oneprovider:
            # WIP
            url = "https://cesnet-oneprovider-01.datahub.egi.eu/api/v3/" + url, headers
        else:
            if "[" in url and "]" in url:
                order_index_start = url.index("[")
                order_index_end = url.index("]")

                order = int(url[order_index_start + 1:order_index_end])
                url = url[:order_index_start] + url[order_index_end + 1:]
            url = Settings.get().ONEPROVIDERS_API_URL[order] + url

    if "oneprovider/" in url:
        headers.update(Settings.get().ONEPROVIDERS_AUTH_HEADERS[order])
    elif "onepanel/" in url:
        headers.update(Settings.get().ONEPANELS_AUTH_HEADERS[order])
    elif "onezone/" in url:
        url = Settings.get().ONEZONE_API_URL + url
        headers.update(Settings.get().ONEZONE_AUTH_HEADERS)
    else:
        Logger.log(1, "No comunication party in URL (%s)" % url)
        return None, None
    return url, headers


def response_print(response, ok_statuses: tuple = tuple()):
    if not response.ok and response.status_code not in ok_statuses:
        Logger.log(2, "Response isn't ok (response code = %s)" % response.status_code)
    debug_print(response, ok_statuses)


def debug_print(response, ok_statuses: tuple = tuple()) -> None:
    if response.content == b"":
        return

    if response.ok or response.status_code in ok_statuses:
        Logger.log(4, "Response: %s" % response)
        Logger.log(5, "Response content:", pretty_print=response.json())
    else:
        Logger.log(1, "Response: %s" % response)
        Logger.log(1, "Response content:", pretty_print=response.json())


def get(url, headers=dict(), ok_statuses: tuple = tuple()):
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
    response_print(response, ok_statuses)
    return response


def patch(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)
    response = requests.patch(url, headers=headers, data=data)
    response_print(response)
    return response


def put(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)
    response = requests.put(url, headers=headers, data=data)
    response_print(response)
    return response


def post(url, headers=dict(), data=dict(), oneprovider=None):
    url, headers = process_url(url, headers, oneprovider)
    response = requests.post(url, headers=headers, data=data)
    response_print(response)
    return response


def delete(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)
    response = requests.delete(url, headers=headers, data=data)
    response_print(response)
    return response
