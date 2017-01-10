#!/bin/bash

pushd `dirname $0` > /dev/null
SCRIPT_DIR=`pwd -P`
popd > /dev/null

PROJECT_NAME=luckyservice

sudo cp "$SCRIPT_DIR/supervisor.conf" "/etc/supervisor/conf.d/$PROJECT_NAME.conf"
sudo supervisorctl update

sudo cp "$SCRIPT_DIR/logrotate.conf" "/etc/logrotate.d/$PROJECT_NAME"

bash $SCRIPT_DIR/restart.sh
