#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=rspamd
PREFIX=${DIR}/../build/snap/${NAME}

rm -rf ${PREFIX}
mkdir -p ${PREFIX}/bin ${PREFIX}/sbin ${PREFIX}/lib ${PREFIX}/etc ${PREFIX}/share

apt-get update
apt-get -y install rspamd

cp /usr/bin/rspamd ${PREFIX}/sbin
cp /usr/bin/rspamc ${PREFIX}/sbin
cp /usr/bin/rspamadm ${PREFIX}/sbin

for binary in ${PREFIX}/sbin/*; do
    ldd ${binary} | awk '/=> \//{print $3}' | while read lib; do
        cp -L --remove-destination ${lib} ${PREFIX}/lib
    done
done

cp $(readlink -f /lib*/ld-linux-*.so*) ${PREFIX}/lib/ld.so

cp -r /etc/rspamd/. ${PREFIX}/etc
cp -r /usr/share/rspamd/. ${PREFIX}/share

rm -rf ${PREFIX}/etc/local.d ${PREFIX}/etc/override.d
mkdir -p ${PREFIX}/etc/local.d ${PREFIX}/etc/override.d

cp ${DIR}/bin/*.sh ${PREFIX}/bin

export LD_LIBRARY_PATH=${PREFIX}/lib
ldd ${PREFIX}/sbin/rspamd
