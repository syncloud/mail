#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

MAJOR_VERSION=9.4-alpine

apt update
apt install -y libltdl7 libnss3


BUILD_DIR=${DIR}/../build/snap/postgresql

docker ps -a -q --filter ancestor=postgres:syncloud --format="{{.ID}}" | xargs docker stop | xargs docker rm || true
docker rmi postgres:syncloud || true
docker build --build-arg MAJOR_VERSION=$MAJOR_VERSION -t postgres:syncloud .
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
./bin/initdb.sh --help
