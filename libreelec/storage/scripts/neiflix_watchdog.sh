#!/bin/bash

BASE_PATH="/storage/.kodi/addons/plugin.video.alfa/"
BASE_URL="https://raw.githubusercontent.com/tonikelope/neiflix/master/libreelec/storage/.kodi/addons/plugin.video.alfa/"

FILES="servers/nei.json servers/nei.py channels/neiflix.py channels/neiflix.json resources/media/channels/banner/neiflix2_b.png resources/media/channels/thumb/neiflix2_t.png resources/media/channels/fanart/neiflix2_f.png"

while [ true ]; do

	set -- $FILES

	while [ -n "$1" ]; do
	    
	    if [ ! -f "${BASE_PATH}${1}" ]; then
			wget "${BASE_URL}${1}" -O "${BASE_PATH}${1}"
		fi

	    shift
	done

	sleep 5

done