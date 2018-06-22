#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [action]"
    exit 1
fi
export LD_LIBRARY_PATH=${DIR}/postfix/lib

case $1 in
start)
    exec $DIR/postfix/usr/sbin/postfix -c ${SNAP_COMMON}/config/postfix start
    ;;
stop)
    exec $DIR/postfix/usr/sbin/postfix -c ${SNAP_COMMON}/config/postfix stop
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
