#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

export LD_LIBRARY_PATH=${DIR}/lib:${DIR}/lib/dovecot
exec ${DIR}/lib/ld.so --library-path ${LD_LIBRARY_PATH} ${DIR}/sbin/dovecot "$@"
