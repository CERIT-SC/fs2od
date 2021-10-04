import json
import re
import time
import setting
from storages import *
from spaces import *
from metadata import *
from tokens import *
from filesystem import *
from groups import *
from shares import *

# #Delete spaces
# for s in getSpaces():
#   if "test" in s['name']:
#     print(s)
#     removeSpace(s['spaceId'])
#     time.sleep(2)

# # # Delete storages
# for s in getStorages()['ids']:
#   name = getStorageDetails(s)['name']
#   if "test" in name:
#     print(name)
#     removeStorage(s)
#     time.sleep(2)

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

## Import subdirs
# import os
# base_path="/volumes/cemcof/external/DATA_21/"
# i = os.scandir(path="./test")

# spaces = list()
# for space in getSpaces():
#     spaces.append(space['name'])

# for e in i: 
#     if e.is_dir():
#         print("Processing: ", e.name)
#         print(base_path + e.name)
#         if not e.name in spaces:
#             dataset_name = e.name
#             storage_id = createAndGetStorage(dataset_name, base_path + e.name)
#             space_id = createAndSupportSpaceForGroup(dataset_name, setting.GROUP_ID, storage_id, 10*2**40) # 10*2**40 = 10 TB
#             print("space id = " + space_id)
#             time.sleep(120)
#             setSpaceMetadataFromYml(space_id)
#             print("*** *** ***")
#             time.sleep(5)
#         else:
#             print(e.name, "exists")

# # Set size of space according to data size
# for s in getSpaces():
#     space_id = s['spaceId']
#     if "_" in s['name'] and s['name'] != "keras_call":
#         setSizeOfSpaceByDataSize(space_id)
#         time.sleep(2)


# sub_dirs = os.scandir(path="test")
# for d in sub_dirs:
#     # write onedata parameters to file
#     space_id="aabbddcc"
#     data = {"onedata": {"spaceId": space_id}}
#     with open(d.path + '/onedata.yml', 'w') as outfile:
#         json.dump(data, outfile, indent=4)


# pprint(getSpaceDetails("bbf8918afa21e6c42c330ec5d03dad37chc1fd"))
# pprint(getAutoStorageImportInfo("bbf8918afa21e6c42c330ec5d03dad37chc1fd"))
# pprint(getContinuousImportStatus("bbf8918afa21e6c42c330ec5d03dad37chc1fd"))
# enableContinuousImport("bbf8918afa21e6c42c330ec5d03dad37chc1fd")
# time.sleep(5)
# pprint(getContinuousImportStatus("bbf8918afa21e6c42c330ec5d03dad37chc1fd"))
# disableContinuousImport("bbf8918afa21e6c42c330ec5d03dad37chc1fd")
# time.sleep(5)
# pprint(getContinuousImportStatus("bbf8918afa21e6c42c330ec5d03dad37chc1fd"))

# gid = createChildGroup(CONFIG['spacesParentGroupId'], "Test aaa bbb")
# print(gid)
# time.sleep(2)
# print(createSpaceForGroup(gid, "Neco 1234"))

#pprint(tokens.createInviteTokenToGroup("350bed3b096956a962e67fac9d1e1bebch7c5c", "Invite token for space test"))
#pprint(createAndGetShare("Jmeno2", "fd2e9fc98f55c09022ffbd202451e3b7ch99dd", description = "Popis"))

#pprint(getSpace("fd2e9fc98f55c09022ffbd202451e3b7ch99dd")['fileId'])
#pprint(getSpaceDetails("fd2e9fc98f55c09022ffbd202451e3b7ch99dd"))

#getSpaces()
#setNewSizeToSpace("25f4c63b04db566006fa83bdbbf4d798cha9f5", 5*2**40)
#setContinuousImport("25f4c63b04db566006fa83bdbbf4d798cha9f5", False)

#token = createNamedTokenForUser("2ab5ac1f4992c6cfb01ec6616f1a94dfch7125", "test-iii", "83d03b05ab8fdca7430b4fa010933630ch8fdc")
#supportSpace(token, 10995116277760, "937a4df9daa22ad10eadf12be640d6ecch70fa")
