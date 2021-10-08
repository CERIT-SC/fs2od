from pprint import pprint
import setting
import filesystem

if setting.DEBUG: pprint(setting.CONFIG['watchedDirectories'])

for d in setting.CONFIG['watchedDirectories']:
    filesystem.scanDirectory(d)
