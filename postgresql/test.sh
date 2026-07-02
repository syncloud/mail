#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/postgresql
${BUILD_DIR}/bin/initdb.sh --version
${BUILD_DIR}/bin/psql.sh --version
${BUILD_DIR}/usr/local/bin/postgres --help
test -f ${DIR}/../build/snap/db.major.version
