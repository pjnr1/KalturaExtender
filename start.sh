#!/bin/bash

LOGFOLDER=/tmp/logs
LOGFILE=${LOGFOLDER}/kaltura-dualstream.log

if [ ! -d "$LOGFOLDER" ]; then
  mkdir ${LOGFOLDER}
fi
if [ ! -f "$LOGFILE" ]; then
  touch ${LOGFILE}
fi


cd /home/KalturaScripts/Production/venv_unix/bin
source activate

cd /home/cronjobs/dualstream/python/

# echo "$(date) starting main.py in $(pwd)"
# echo "$(date): python $(pwd)/main.py" >> $LOGFILE
python main.py >> ${LOGFILE}

deactivate
