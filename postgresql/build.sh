#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

MAJOR_VERSION=9.4-alpine
BUILD_DIR=${DIR}/../build/snap/postgresql

postgres --help

rm -rf ${BUILD_DIR}
mkdir -p ${BUILD_DIR}
echo "${MAJOR_VERSION}" > ${BUILD_DIR}/../db.major.version
cp -r /etc ${BUILD_DIR}
cp -r /usr ${BUILD_DIR}
cp -r /bin ${BUILD_DIR}
cp -r /lib ${BUILD_DIR}

cd ${BUILD_DIR}
PGBIN=$(echo usr/local/bin)
ldd $PGBIN/initdb
mv $PGBIN/postgres $PGBIN/postgres.bin
mv $PGBIN/pg_dump $PGBIN/pg_dump.bin
cp $DIR/bin/* bin
cp $DIR/pgbin/* $PGBIN
