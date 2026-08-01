#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

exec ${DIR}/opendkim/bin/opendkim.sh -x ${SNAP_DATA}/config/opendkim/opendkim.conf
