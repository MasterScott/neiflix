
### NEIFLIX START ###
(/storage/scripts/neiflix_watchdog.sh 2>&1 > /var/log/neiflix_watchdog.log) &
(/usr/bin/python /storage/scripts/neiflix_updater.py 2>&1 > /var/log/neiflix_updater.log) &
### NEIFLIX END ###
