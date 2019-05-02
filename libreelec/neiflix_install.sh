#!/bin/bash

echo "Downloading NEIFLIX..."
wget https://github.com/tonikelope/neiflix/archive/master.zip -O /tmp/neiflix_master.zip

echo "Unzipping..."
unzip /tmp/neiflix_master.zip -d /tmp

echo "Copying files..."
mv /storage/.config/autostart.sh /storage/.config/autostart.sh.bak
cp -rvf /tmp/neiflix-master/libreelec/storage/.config/ /storage/
cp -rvf /tmp/neiflix-master/libreelec/storage/scripts/ /storage/
cp -rvf /tmp/neiflix-master/libreelec/storage/.kodi/ /storage/

echo "Cleaning..."
rm -rf /tmp/neiflix-master/
rm -rf /tmp/neiflix_master.zip

echo -e "\nNEIFLIX INSTALLED!"