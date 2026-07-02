#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

OPENDKIM=${DIR}/../build/snap/opendkim
export LD_LIBRARY_PATH=${OPENDKIM}/lib
ldd ${OPENDKIM}/sbin/opendkim

${OPENDKIM}/bin/opendkim.sh -V
${OPENDKIM}/bin/opendkim-genkey --help
