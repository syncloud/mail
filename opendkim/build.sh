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

for nss in libnss_files.so.2 libnss_compat.so.2 libnss_dns.so.2; do
    found=$(find /usr/lib /lib -maxdepth 3 -name "$nss" -print -quit 2>/dev/null)
    if [ -z "${found}" ]; then
        echo "opendkim: nss module not found: $nss"
        exit 1
    fi
    cp -L --remove-destination "${found}" ${PREFIX}/lib
done

cp /usr/sbin/opendkim $PREFIX/sbin
find /usr/bin /usr/sbin -maxdepth 1 -name 'opendkim-*' -exec cp {} $PREFIX/bin \;

cp ${DIR}/bin/* $PREFIX/bin

export LD_LIBRARY_PATH=${PREFIX}/lib
ldd $PREFIX/sbin/opendkim
$PREFIX/sbin/opendkim -V
$PREFIX/bin/opendkim-genkey --help
