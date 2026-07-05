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

cp -L --remove-destination /lib/*-linux-gnu*/libc.so.6 ${PREFIX}/lib
cp -L --remove-destination /lib/*-linux-gnu*/libdl.so.2 ${PREFIX}/lib
cp -L --remove-destination /lib/*-linux-gnu*/libgcc_s.so.1 ${PREFIX}/lib
cp -L --remove-destination /lib/*-linux-gnu*/libm.so.6 ${PREFIX}/lib
cp -L --remove-destination /lib/*-linux-gnu*/libpthread.so.0 ${PREFIX}/lib
cp -L --remove-destination /lib/*-linux-gnu*/libresolv.so.2 ${PREFIX}/lib
cp -L --remove-destination /lib/*-linux-gnu*/libnss_files.so.2 ${PREFIX}/lib
cp -L --remove-destination /lib/*-linux-gnu*/libnss_compat.so.2 ${PREFIX}/lib
cp -L --remove-destination /lib/*-linux-gnu*/libnss_dns.so.2 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libbsd.so.0 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libcrypto.so.1.1 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libdb-5.3.so ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libevent-2.1.so.7 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libffi.so.7 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libgmp.so.10 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libgnutls.so.30 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libhogweed.so.6 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libidn2.so.0 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/liblber-2.4.so.2 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libldap_r-2.4.so.2 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/liblua5.1.so.0 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libmd.so.0 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libmemcached.so.11 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libmilter.so.1.0.1 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libnettle.so.8 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libopendkim.so.11 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libp11-kit.so.0 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/librbl.so.1 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libsasl2.so.2 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libssl.so.1.1 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libstdc++.so.6 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libtasn1.so.6 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libunbound.so.8 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libunistring.so.2 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/*-linux-gnu*/libvbr.so.2 ${PREFIX}/lib
cp -L --remove-destination /usr/lib/libopendbx.so.1 ${PREFIX}/lib

cp /usr/sbin/opendkim ${PREFIX}/sbin
cp /usr/sbin/opendkim-genkey ${PREFIX}/bin
cp ${DIR}/bin/* ${PREFIX}/bin

export LD_LIBRARY_PATH=${PREFIX}/lib
ldd ${PREFIX}/sbin/opendkim
${PREFIX}/bin/opendkim.sh -V
${PREFIX}/bin/opendkim-genkey --help
