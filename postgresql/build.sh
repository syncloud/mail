#!/bin/sh -ex

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

MAJOR_VERSION=9.4-alpine
BUILD_DIR=${DIR}/../build/snap/postgresql

while ! docker build --build-arg MAJOR_VERSION=$MAJOR_VERSION -t postgres:syncloud . ; do
  echo "retry"
  sleep 1
done
docker run postgres:syncloud postgres --help
docker create --name=postgres postgres:syncloud
mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
echo "${MAJOR_VERSION}" > ${BUILD_DIR}/../db.major.version
docker export postgres -o postgres.tar
tar xf postgres.tar
rm -rf postgres.tar
PGBIN=$(echo usr/local/bin)
ldd $PGBIN/initdb
mv $PGBIN/postgres $PGBIN/postgres.bin
mv $PGBIN/pg_dump $PGBIN/pg_dump.bin
cp $DIR/bin/* bin
cp $DIR/pgbin/* $PGBIN
