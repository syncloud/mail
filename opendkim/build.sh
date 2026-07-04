#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=opendkim
PREFIX=${DIR}/../build/snap/${NAME}

rm -rf ${PREFIX}
mkdir -p ${PREFIX}/bin ${PREFIX}/sbin ${PREFIX}/lib

apt-get update
apt-get -y install opendkim opendkim-tools

cp $(readlink -f /lib*/ld-linux-*.so*) ${PREFIX}/lib/ld.so

for lib in \
    libc.so.6 \
    libdl.so.2 \
    libgcc_s.so.1 \
    libm.so.6 \
    libpthread.so.0 \
    libresolv.so.2 \
    libnss_files.so.2 \
    libnss_compat.so.2 \
    libnss_dns.so.2; do
    cp -L --remove-destination /lib/*-linux-gnu*/${lib} ${PREFIX}/lib
done

for lib in \
    libbsd.so.0 \
    libcrypto.so.1.1 \
    libdb-5.3.so \
    libevent-2.1.so.7 \
    libffi.so.7 \
    libgmp.so.10 \
    libgnutls.so.30 \
    libhogweed.so.6 \
    libidn2.so.0 \
    liblber-2.4.so.2 \
    libldap_r-2.4.so.2 \
    liblua5.1.so.0 \
    libmd.so.0 \
    libmemcached.so.11 \
    libmilter.so.1.0.1 \
    libnettle.so.8 \
    libopendkim.so.11 \
    libp11-kit.so.0 \
    librbl.so.1 \
    libsasl2.so.2 \
    libssl.so.1.1 \
    libstdc++.so.6 \
    libtasn1.so.6 \
    libunbound.so.8 \
    libunistring.so.2 \
    libvbr.so.2; do
    cp -L --remove-destination /usr/lib/*-linux-gnu*/${lib} ${PREFIX}/lib
done

cp -L --remove-destination /usr/lib/libopendbx.so.1 ${PREFIX}/lib

cp /usr/sbin/opendkim ${PREFIX}/sbin
cp /usr/sbin/opendkim-genkey ${PREFIX}/bin
cp ${DIR}/bin/* ${PREFIX}/bin

export LD_LIBRARY_PATH=${PREFIX}/lib
ldd ${PREFIX}/sbin/opendkim
${PREFIX}/bin/opendkim.sh -V
${PREFIX}/bin/opendkim-genkey --help
