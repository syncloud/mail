#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
PREFIX=${DIR}/../build/snap/postfix

du -d10 -h $PREFIX | sort -h | tail -100

ldd ${PREFIX}/usr/sbin/postfix
ls -la ${PREFIX}/bin
${PREFIX}/bin/postfix.sh --help || true
${PREFIX}/bin/postconf.sh -a
${PREFIX}/bin/postconf.sh -A
