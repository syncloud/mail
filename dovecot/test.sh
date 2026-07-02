#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DOVECOT=${DIR}/../build/snap/dovecot

${DOVECOT}/bin/dovecot.sh --version
${DOVECOT}/bin/doveadm.sh 2>&1 | grep "doveadm(init)"
${DOVECOT}/libexec/dovecot/auth.sh 2>&1 | grep "auth(init)"

export LD_LIBRARY_PATH=${DOVECOT}/lib:${DOVECOT}/lib/dovecot:${DOVECOT}/lib/dovecot/old-stats
ldd ${DOVECOT}/libexec/dovecot/auth
${DOVECOT}/libexec/dovecot/auth 2>&1 | grep "auth(init)"
