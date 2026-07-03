#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=opendkim
PREFIX=${DIR}/../build/snap/${NAME}

rm -rf ${PREFIX}
mkdir -p ${PREFIX}/bin
mkdir -p ${PREFIX}/sbin
mkdir -p ${PREFIX}/lib

apt-get update
apt-get -y install opendkim opendkim-tools

copy_deps() {
    ldd "$1" 2>/dev/null | awk '$2 == "=>" && $3 ~ /^\// {print $3} $1 ~ /^\// && $2 != "=>" {print $1}'
}

cp $(readlink -f /lib*/ld-linux-*.so*) ${PREFIX}/lib/ld.so

for bin in /usr/sbin/opendkim \
           /usr/bin/opendkim-atpszone \
           /usr/bin/opendkim-genzone \
           /usr/bin/opendkim-spam \
           /usr/bin/opendkim-stats \
           /usr/bin/opendkim-testkey \
           /usr/bin/opendkim-testmsg \
           /usr/bin/convert_keylist \
           /usr/bin/miltertest; do
    copy_deps "$bin"
done | sort -u | while read -r lib; do
    cp -L --remove-destination "$lib" ${PREFIX}/lib
done

cp /usr/sbin/opendkim $PREFIX/sbin
cp /usr/bin/convert_keylist $PREFIX/bin
cp /usr/bin/miltertest $PREFIX/bin
cp /usr/bin/opendkim-atpszone $PREFIX/bin
cp /usr/bin/opendkim-genkey $PREFIX/bin
cp /usr/bin/opendkim-genzone $PREFIX/bin
cp /usr/bin/opendkim-spam $PREFIX/bin
cp /usr/bin/opendkim-stats $PREFIX/bin
cp /usr/bin/opendkim-testkey $PREFIX/bin
cp /usr/bin/opendkim-testmsg $PREFIX/bin

cp ${DIR}/bin/* $PREFIX/bin

export LD_LIBRARY_PATH=${PREFIX}/lib
ldd $PREFIX/sbin/opendkim
$PREFIX/sbin/opendkim -V
$PREFIX/bin/opendkim-genkey --help
