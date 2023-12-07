#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

/bin/rm -f ${SNAP_COMMON}/web.socket
exec ${DIR}/nginx/sbin/nginx -c ${SNAP_COMMON}/config/nginx/nginx.conf -p ${DIR}/nginx -e stderr
