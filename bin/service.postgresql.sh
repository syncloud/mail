#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi

case $1 in
start)
    exec ${DIR}/postgresql/bin/pg_ctl.sh -w -s -D ${SNAP_COMMON}/database start
    ;;
stop)
    exec ${DIR}/postgresql/bin/pg_ctl.sh -s -D ${SNAP_COMMON}/database stop -m fast
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
