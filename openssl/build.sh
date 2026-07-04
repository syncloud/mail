#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

PREFIX=${DIR}/../test/openssl
rm -rf ${PREFIX}
mkdir -p ${PREFIX}/bin ${PREFIX}/lib

sed -i -e 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' \
       -e 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' \
       -e 's|http://deb.debian.org/debian-security|http://archive.debian.org/debian-security|g' \
       -e '/buster-updates/d' /etc/apt/sources.list
apt-get -o Acquire::Check-Valid-Until=false update
apt-get -y install openssl

cp /usr/bin/openssl ${PREFIX}/bin/openssl.bin
cp -a /lib/*-linux-gnu*/. ${PREFIX}/lib/
cp /usr/lib/*/libssl.so* ${PREFIX}/lib/
cp /usr/lib/*/libcrypto.so* ${PREFIX}/lib/
cp ${DIR}/openssl ${PREFIX}/bin/openssl
