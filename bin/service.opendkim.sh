#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [action]"
    exit 1
fi

case $1 in
start)
    exec $DIR/opendkim/bin/opendkim.sh -x ${SNAP_COMMON}/config/opendkim/opendkim.conf
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
