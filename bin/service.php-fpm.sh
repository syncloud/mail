#!/bin/bash

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

if [[ -z "$1" ]]; then
    echo "usage $0 [start]"
    exit 1
fi

case $1 in
start)
    exec $DIR/php/bin/php-fpm.sh -y ${SNAP_DATA}/config/php/php-fpm.conf -c ${SNAP_DATA}/config/php/php.ini
    ;;
post-start)
    timeout 5 /bin/bash -c 'until [ -S '${SNAP_DATA}'/log/php5-fpm.sock ]; do echo "waiting for ${SNAP_DATA}/log/php5-fpm.sock"; sleep 1; done'
    ;;
*)
    echo "not valid command"
    exit 1
    ;;
esac
