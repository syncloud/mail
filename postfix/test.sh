#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PREFIX=${DIR}/../build/snap/postfix
ldd ${PREFIX}/usr/sbin/postfix

${PREFIX}/bin/postfix.sh --help || true
${PREFIX}/bin/postconf.sh -a
${PREFIX}/bin/postconf.sh -A
