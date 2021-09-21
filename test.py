import json
import re
import time
import setting
from storages import *
from spaces import *
from metadata import *
from tokens import *

# #Delete spaces
# for s in getSpaces():
#   if "_" in s['name'] and not "keras_call" == s['name']:
#     print(s)
#     removeSpace(s['spaceId'])
# time.sleep(5)

# # Delete storages
# for s in getStorages()['ids']:
#   name = getStorageDetails(s)['name']
#   if "_" in name:
#     print(name)
#     removeStorage(s)

# #Remove tokens
# for token_id in listAllNamedtokens():
#   token_name = getNamedToken(token_id)['name']
#   if "Token_for_" in token_name:
#     print(token_name)
#     deleteNamedToken(token_id)

## Tests
# print(getStorageDetails("26e5815a5cc101a1eb62d8bc049066dach6754"))
# print(getSpaces())
# print(getSpace("f75538557a10a446e2d2daa070a87927chf745"))
# print(downloadFileContent("000000000052771967756964236438626539336466383634663165346638363865393334633461656530303065636832336264233362366266326630356331396539326561646638643966373238306230373333636830373137"))
# print(listDirectory("00000000005841B0677569642373706163655F3362366266326630356331396539326561646638643966373238306230373333636830373137233362366266326630356331396539326561646638643966373238306230373333636830373137"))
# print(createSpaceForGroup("d18ef1c21bb64d59b7e9e57fb12031c0chb64d", "Test vytvareni"))

# id = createAndGetStorage("jmeno22", "/cesta")
# print(id)
# print(removeStorage(id))

#pprint(getSpaces())

#dataset_name = "jmeno123"
#storage_id = createAndGetStorage(dataset_name, "/volumes/cemcof/external/DATA_21/210820_galactosidase")
#createAndSupportSpaceForGroup(dataset_name, "d18ef1c21bb64d59b7e9e57fb12031c0chb64d", storage_id, 10*2**40) # 10*2**40 = 10 TB

#print(removeStorage(storage_id))


# get space details
#res = getSpace("cd8b5b27d9ce42b49f318782daaf1185ch93e6")
#file_id = res['fileId']

#setSpaceMetadataFromYml("cd8b5b27d9ce42b49f318782daaf1185ch93e6")

# Import subdirs
# import os
# base_path="/volumes/cemcof/external/DATA_21/"
# i = os.scandir(path="./test")
# for e in i: 
#   if e.is_dir(): 
#     print("Processing: ", e.name)
#     print(base_path + e.name)
#     dataset_name = e.name
#     storage_id = createAndGetStorage(dataset_name, base_path + e.name)
#     space_id = createAndSupportSpaceForGroup(dataset_name, setting.GROUP_ID, storage_id, 5*2**40) # 10*2**40 = 10 TB
#     print("space id = " + space_id)
#     time.sleep(5)
#     setSpaceMetadataFromYml(space_id)
#     print("*** *** ***")
