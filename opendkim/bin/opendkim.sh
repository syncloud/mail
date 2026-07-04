#!/bin/bash -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
export LD_LIBRARY_PATH=${DIR}/lib
exec ${DIR}/lib/ld.so --library-path ${DIR}/lib ${DIR}/sbin/opendkim "$@"
