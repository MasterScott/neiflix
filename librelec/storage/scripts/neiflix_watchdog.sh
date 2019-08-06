#!/bin/bash

BASE_PATH="/storage/.kodi/addons/plugin.video.alfa/"
BASE_URL="https://raw.githubusercontent.com/tonikelope/neiflix/master/plugin.video.alfa/"

FILES="channels/neiflix.py channels/neiflix.json resources/media/channels/banner/neiflix2_b.png resources/media/channels/thumb/neiflix2_t.png resources/media/channels/fanart/neiflix2_f.png"

while [ true ]; do

	set -- $FILES

	while [ -n "$1" ]; do
	    
	    if [ ! -f "${BASE_PATH}${1}" ]; then
			wget "${BASE_URL}${1}" -O "${BASE_PATH}${1}"
		fi

	    shift
	done

	sha1_hash=$(sha1sum "${BASE_PATH}servers/mega.py" | grep -E -o '[a-f0-9]+' | head -1)

	if [ "$sha1_hash" != "f1a30a53f0160014b614569e9c44d92dc0b32628" ]; then

		wget "${BASE_URL}servers/mega.py" -O "${BASE_PATH}servers/mega.py"

	fi

	sleep 5

done