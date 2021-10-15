#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [action]"
    exit 1
fi

export DOVECOT_BINDIR=${DIR}/dovecot/bin
case $1 in
start)
    /bin/rm -rf ${SNAP_COMMON}/dovecot/master.pid
    exec $DIR/dovecot/bin/dovecot.sh -F -c ${SNAP_COMMON}/config/dovecot/dovecot.conf
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
