#!/bin/bash

PROJECT_HOME=/home/ubuntu/af-env/luckyservice
VIRENV_BIN_DIR=/home/ubuntu/af-env/bin

#pkill -f "processor.py"
#pkill -f "celery -A luckycommon.async"

cd $PROJECT_HOME
#nohup sudo -u ubuntu $VIRENV_BIN_DIR/python $PROJECT_HOME/luckycommon/timer/processor.py >/dev/null 2>&1 &
#nohup sudo -u ubuntu $VIRENV_BIN_DIR/celery -A luckycommon.async worker -c 2 -l info --autoreload >/dev/null 2>&1 &

#supervisorctl restart luckyservice
