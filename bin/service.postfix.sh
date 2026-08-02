#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

export SASL_PATH=${DIR}/postfix/lib/sasl2
exec ${DIR}/postfix/bin/postfix.sh -c ${SNAP_DATA}/config/postfix start
