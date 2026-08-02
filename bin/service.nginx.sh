#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

/bin/rm -f ${SNAP_COMMON}/web.socket
exec ${DIR}/nginx/bin/nginx.sh -c ${SNAP_DATA}/config/nginx/nginx.conf -p ${DIR}/nginx -e stderr
