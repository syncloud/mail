#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [action]"
    exit 1
fi

export LD_LIBRARY_PATH=${DIR}/opendkim/lib

case $1 in
start)
    exec $DIR/opendkim/sbin/opendkim -x ${SNAP_COMMON}/config/opendkim/opendkim.conf
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
