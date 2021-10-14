#!/usr/bin/env python3

from pprint import pprint
import setting
import filesystem

if setting.DEBUG >= 2: print("Directories to check:")
if setting.DEBUG >= 2: pprint(setting.CONFIG['watchedDirectories'])

for d in setting.CONFIG['watchedDirectories']:
    filesystem.scanDirectory(d)
