# -*- coding: utf-8 -*-

import urllib
import re
import os
import hashlib

KODI_PATH = '/storage/.kodi/'
UPDATE_URL = 'https://raw.githubusercontent.com/tonikelope/neiflix/master/libreelec/storage/.kodi/addons/plugin.video.alfa/channels/'

urllib.urlretrieve(UPDATE_URL + 'checksum.sha1', KODI_PATH + 'temp/neiflix_channel.sha1')

sha1_checksums = {}

with open(KODI_PATH + 'temp/neiflix_channel.sha1') as f:
    for line in f:
        strip_line = line.strip()
        if strip_line:
            parts = re.split(' +', line.strip())
            sha1_checksums[parts[1]]=parts[0]

for filename, checksum in sha1_checksums.iteritems():
	with open(KODI_PATH + 'addons/plugin.video.alfa/channels/' + filename, 'rb') as f:
		if hashlib.sha1(f.read()).hexdigest() != checksum:
			urllib.urlretrieve(UPDATE_URL + filename, KODI_PATH + 'addons/plugin.video.alfa/channels/' + filename)
			print('NEIFLIX_UPDATER -> '+filename+' updated!')

os.remove(KODI_PATH + 'temp/neiflix_channel.sha1')
