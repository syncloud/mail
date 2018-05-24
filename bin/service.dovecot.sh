#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [action]"
    exit 1
fi

export LD_LIBRARY_PATH=${DIR}/dovecot/lib/dovecot
export DOVECOT_BINDIR=${DIR}/dovecot/bin
case $1 in
pre-start)
    /bin/rm -rf ${SNAP_COMMON}/dovecot/master.pid
    ;;
start)
    exec $DIR/dovecot/sbin/dovecot -F -c ${SNAP_COMMON}/config/dovecot/dovecot.conf
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
