#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DOVECOT=${DIR}/../build/snap/dovecot

${DOVECOT}/bin/dovecot.sh --version
