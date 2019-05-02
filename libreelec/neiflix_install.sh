#!/bin/bash

echo "Downloading NEIFLIX..."
wget https://github.com/tonikelope/neiflix/archive/master.zip -O /tmp/neiflix_master.zip

echo "Unzipping..."
unzip /tmp/neiflix_master.zip -d /tmp

echo "Copying files..."

if [-z "$(cat /storage/.config/autostart.sh | grep neiflix)"]; then
	cat /tmp/neiflix-master/libreelec/storage/.config/autostart.sh >> /storage/.config/autostart.sh
fi

cp -rvf /tmp/neiflix-master/libreelec/storage/scripts/ /storage/
cp -rvf /tmp/neiflix-master/libreelec/storage/.kodi/ /storage/

echo "Cleaning..."
rm -rf /tmp/neiflix-master/
rm -rf /tmp/neiflix_master.zip

echo -e "\nNEIFLIX INSTALLED!"