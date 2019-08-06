#!/bin/bash

BASE_PATH="/storage/.kodi/addons/plugin.video.alfa/"
BASE_URL="https://raw.githubusercontent.com/tonikelope/neiflix/master/libreelec/storage/.kodi/addons/plugin.video.alfa/"

FILES="channels/neiflix.py channels/neiflix.json resources/media/channels/banner/neiflix2_b.png resources/media/channels/thumb/neiflix2_t.png resources/media/channels/fanart/neiflix2_f.png"

wget "${BASE_URL}servers/mega_checksum.sha1" -O "/tmp/mega_checksum.sha1"

while [ true ]; do

	set -- $FILES

	while [ -n "$1" ]; do
	    
	    if [ ! -f "${BASE_PATH}${1}" ]; then
			wget "${BASE_URL}${1}" -O "${BASE_PATH}${1}"
		fi

	    shift
	done

	cd "${BASE_PATH}servers/"

	sha1sum -c "/tmp/mega_checksum.sha1"

	if [ $? -eq 1 ]; then

		wget "${BASE_URL}servers/mega.py" -O "${BASE_PATH}servers/mega.py"

	fi

	sleep 5

done