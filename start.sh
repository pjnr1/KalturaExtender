#!/bin/bash


cd /home/KalturaScripts/Production/venv_unix/bin
source activate

cd /home/cronjobs/dualstream/python/

# echo "$(date) starting main.py in $(pwd)"
python main.py

deactivate
