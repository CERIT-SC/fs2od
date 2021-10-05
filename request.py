from pprint import pprint
import requests
import setting

def process_url(url, headers):
    if "oneprovider/" in url:
        url = setting.ONEPROVIDER_API_URL + url
        headers.update(setting.ONEPROVIDER_AUTH_HEADERS)
    elif "onepanel/" in url:
        url = setting.ONEPANEL_API_URL + url
        headers.update(setting.ONEPANEL_AUTH_HEADERS)
    elif "onezone/" in url:
        url = setting.ONEZONE_API_URL + url
        headers.update(setting.ONEZONE_AUTH_HEADERS)
    else:
        print("Error: no comunication party in url")
        return None
    return url, headers

def response_print(response):
    if setting.DEBUG >= 1:
        if not response.ok:
            print("Warning: response is not ok, response code", response.status_code)

def debug_print(response):
    if setting.DEBUG >= 3:
        print(response)
        if response.content != b'':
            pprint(response.json())

def get(url, headers=dict()):
    url, headers = process_url(url, headers)
    response = requests.get(url, headers=headers, verify=False)
    response_print(response)
    debug_print(response)
    return response

def patch(url, headers=dict(), data=dict()):
    url, headers = process_url(url, headers)    
    response = requests.patch(url, headers=headers, data=data, verify=False)
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
