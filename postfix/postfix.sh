#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )
LD_LIBRARY_PATH=$(find ${DIR}/lib ${DIR}/usr/lib -type d | tr '\n' ':')
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH%:}
exec ${DIR}/usr/sbin/postfix "$@"