#!/bin/bash

pushd `dirname $0` > /dev/null
SCRIPT_DIR=`pwd -P`
popd > /dev/null

ACTION=deploy
RESTART=1
ENVR=sluck
HOST=test
DEBUG=0

usage()
{
    echo "Usage: `basename $0` [-b|f] [-p] [-r] [-d] [-h HOST]"
    exit 1
}

[ $# -eq 0 ] && usage

while getopts :bdfprh: OPTION
do
    case $OPTION in
        b)
            ENVR=sluck
            ;;
        d)
            DEBUG=1
            ;;
        f)
            ENVR=luckyweb
            ;;
        p)
            ACTION=envinstall
            ;;
        r)
            RESTART=0
            ;;
        h)
            HOST=$OPTARG
            ;;
        \?)
            usage
            ;;
    esac
done


(
    cd $SCRIPT_DIR
    fab dep:$HOST pro:$ENVR $ACTION:$RESTART --set debug=$DEBUG
)
