#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=redis
PREFIX=${DIR}/../build/snap/${NAME}

rm -rf ${PREFIX}
mkdir -p ${PREFIX}/bin ${PREFIX}/sbin ${PREFIX}/lib

apt-get update
apt-get -y install redis-server

cp /usr/bin/redis-server ${PREFIX}/sbin
cp /usr/bin/redis-cli ${PREFIX}/sbin

for binary in ${PREFIX}/sbin/*; do
    ldd ${binary} | awk '/=> \//{print $3}' | while read lib; do
        cp -L --remove-destination ${lib} ${PREFIX}/lib
    done
done

cp $(readlink -f /lib*/ld-linux-*.so*) ${PREFIX}/lib/ld.so

cp ${DIR}/bin/*.sh ${PREFIX}/bin

export LD_LIBRARY_PATH=${PREFIX}/lib
ldd ${PREFIX}/sbin/redis-server
