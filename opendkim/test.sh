#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

OPENDKIM=${DIR}/../build/snap/opendkim
${OPENDKIM}/bin/opendkim.sh -V
