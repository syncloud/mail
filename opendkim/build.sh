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

ldd /usr/sbin/opendkim | awk '/=> \//{print $3}' | xargs -I{} cp -L --remove-destination {} ${PREFIX}/lib
for lib in libnss_files libnss_compat libnss_dns; do
  cp -L --remove-destination /lib/*-linux-gnu*/${lib}.so.2 ${PREFIX}/lib
done

cp /usr/sbin/opendkim ${PREFIX}/sbin
cp /usr/sbin/opendkim-genkey ${PREFIX}/bin
cp ${DIR}/bin/* ${PREFIX}/bin

export LD_LIBRARY_PATH=${PREFIX}/lib
ldd ${PREFIX}/sbin/opendkim
${PREFIX}/bin/opendkim.sh -V
${PREFIX}/bin/opendkim-genkey --help
