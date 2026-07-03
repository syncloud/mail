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

copylib() {
    local found
    found=$(find /usr/lib /lib -maxdepth 3 -name "$1" -print -quit 2>/dev/null)
    if [ -z "${found}" ]; then
        echo "opendkim: library not found: $1"
        exit 1
    fi
    cp "${found}" ${PREFIX}/lib
}

cp $(readlink -f /lib*/ld-linux-*.so*) ${PREFIX}/lib/ld.so

copylib libopendkim.so.11
copylib libmilter.so.1.0.1
copylib libssl.so.1.1
copylib libcrypto.so.1.1
copylib libresolv.so.2
copylib libdb-5.3.so
copylib libopendbx.so.1
copylib libdl.so.2
copylib libmemcached.so.11
copylib libmemcachedutil.so.2
copylib liblua5.1.so.0
copylib libldap_r-2.4.so.2
copylib liblber-2.4.so.2
copylib libunbound.so.8
copylib libvbr.so.2
copylib librbl.so.1
copylib libbsd.so.0
copylib libpthread.so.0
copylib libc.so.6
copylib libsasl2.so.2
copylib libstdc++.so.6
copylib libm.so.6
copylib libgcc_s.so.1
copylib libgnutls.so.30
copylib libevent-2.1.so.6
copylib libhogweed.so.4
copylib libnettle.so.6
copylib libgmp.so.10
copylib librt.so.1
copylib libp11-kit.so.0
copylib libidn2.so.0
copylib libunistring.so.2
copylib libtasn1.so.6
copylib libffi.so.6

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
