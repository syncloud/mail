#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

NAME=openssl
PREFIX=${DIR}/../test/openssl
OPENSSL_VERSION=1.1.1h

apt-get update
apt-get -y install build-essential libffi-dev wget

rm -rf ${PREFIX}
mkdir -p ${PREFIX}

rm -rf ${DIR}/work
mkdir -p ${DIR}/work
cd ${DIR}/work

wget https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz --progress dot:giga

tar xzf openssl-${OPENSSL_VERSION}.tar.gz
cd openssl-${OPENSSL_VERSION}

if [ "$(dpkg --print-architecture)" = "armhf" ]; then
    ./Configure linux-generic32 --prefix=${PREFIX} --openssldir=/usr/lib/ssl no-shared no-ssl2 no-ssl3 no-asm -fPIC
else
    ./config --prefix=${PREFIX} --openssldir=/usr/lib/ssl no-shared no-ssl2 no-ssl3 no-asm -fPIC
fi
make
make install

mv ${PREFIX}/bin/openssl ${PREFIX}/bin/openssl.bin
cp ${DIR}/openssl ${PREFIX}/bin/openssl

${PREFIX}/bin/openssl version -a
