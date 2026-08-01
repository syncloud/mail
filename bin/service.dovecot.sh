#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

export DOVECOT_BINDIR=${DIR}/dovecot/bin
/bin/rm -rf ${SNAP_DATA}/dovecot/master.pid
exec ${DIR}/dovecot/bin/dovecot.sh -F -c ${SNAP_DATA}/config/dovecot/dovecot.conf
