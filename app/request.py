from pprint import pprint
import requests
import urllib3
from settings import Settings

# HACK - disable warnings when curl can't verify the remote server by its certificate. Fix before production.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def process_url(url, headers):
    if "oneprovider/" in url:
        url = Settings.get().ONEPROVIDER_API_URL + url
        headers.update(Settings.get().ONEPROVIDER_AUTH_HEADERS)
    elif "onepanel/" in url:
        url = Settings.get().ONEPANEL_API_URL + url
        headers.update(Settings.get().ONEPANEL_AUTH_HEADERS)
    elif "onezone/" in url:
        url = Settings.get().ONEZONE_API_URL + url
        headers.update(Settings.get().ONEZONE_AUTH_HEADERS)
    else:
        print("Error: no comunication party in url")
        return None
    return url, headers

def response_print(response):
    if Settings.get().debug >= 1:
        if not response.ok:
            print("Warning: response is not ok, response code", response.status_code)

def debug_print(response):
    if Settings.get().debug >= 3:
        print(response)
        if response.content != b'':
            pprint(response.json())

def get(url, headers=dict()):
    url, headers = process_url(url, headers)
    timeout_counter = 3
    response = requests.get(url, headers=headers, verify=False)
    # commented because not ok is sometimes right response 
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
    response = requests.patch(url, headers=headers, data=data, verify=False)
    response_print(response)
    debug_print(response)
    return response

def put(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)    
    response = requests.put(url, headers=headers, data=data, verify=False)
    response_print(response)
    debug_print(response)
    return response

def post(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)    
    response = requests.post(url, headers=headers, data=data, verify=False)
    response_print(response)
    debug_print(response)
    return response

def delete(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)    
    response = requests.delete(url, headers=headers, data=data, verify=False)
    response_print(response)
    debug_print(response)
    return response
