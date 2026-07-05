#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=dovecot
VERSION=$1
PREFIX=/snap/mail/current/${NAME}
OUTPUT=${DIR}/../build/snap/${NAME}

apt-get update
apt-get -y install build-essential libncurses5-dev libldap2-dev libsasl2-dev libssl-dev libldb-dev wget

rm -rf ${PREFIX}
mkdir -p ${PREFIX}

rm -rf ${DIR}/work
mkdir -p ${DIR}/work
cd ${DIR}/work

wget http://www.dovecot.org/releases/2.3/${NAME}-${VERSION}.tar.gz --progress dot:giga
tar xzf ${NAME}-${VERSION}.tar.gz
cd ${NAME}-${VERSION}

./configure --prefix=${PREFIX} \
    --with-rawlog \
    --with-ldap \
    --disable-rpath

make -j4
make install

echo "original libs"
ldd ${PREFIX}/sbin/dovecot

cp --remove-destination /usr/lib/*/libssl*.so* ${PREFIX}/lib/dovecot
cp --remove-destination /lib/*/libcrypt.so* ${PREFIX}/lib/dovecot
cp --remove-destination /usr/lib/*/libcrypto.so* ${PREFIX}/lib/dovecot
cp -a /lib/*-linux-gnu*/. ${PREFIX}/lib/
cp --remove-destination /usr/lib/*/libldap*.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/liblber*.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libsasl2.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libgnutls.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libp11-kit.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libidn2.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libunistring.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libtasn1.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libnettle.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libhogweed.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libgmp.so* ${PREFIX}/lib
cp --remove-destination /usr/lib/*/libffi.so* ${PREFIX}/lib

cp $(readlink -f /lib*/ld-linux-*.so*) ${PREFIX}/lib/ld.so

echo "embedded libs"
export LD_LIBRARY_PATH=${PREFIX}/lib
ldd ${PREFIX}/sbin/dovecot
ldd ${PREFIX}/libexec/dovecot/auth

cp ${DIR}/dovecot.sh ${PREFIX}/bin
cp ${DIR}/lda.sh ${PREFIX}/bin
cp ${DIR}/doveadm.sh ${PREFIX}/bin
cp ${DIR}/auth.sh ${PREFIX}/libexec/dovecot

apt-get -y install patchelf
INTERP=/snap/mail/current/dovecot/lib/ld.so
RPATH=/snap/mail/current/dovecot/lib:/snap/mail/current/dovecot/lib/dovecot
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/sbin/dovecot
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/bin/doveadm
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/bin/doveconf
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/aggregator
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/anvil
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/auth
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/checkpassword-reply
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/config
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/dict
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/director
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/dns-client
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/doveadm-server
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/dovecot-lda
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/gdbhelper
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/imap
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/imap-hibernate
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/imap-login
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/imap-urlauth
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/imap-urlauth-login
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/imap-urlauth-worker
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/indexer
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/indexer-worker
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/ipc
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/lmtp
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/log
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/maildirlock
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/old-stats
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/pop3
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/pop3-login
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/quota-status
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/rawlog
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/replicator
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/script
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/script-login
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/stats
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/submission
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/submission-login
patchelf --set-interpreter "$INTERP" --set-rpath "$RPATH" --force-rpath ${PREFIX}/libexec/dovecot/xml2text

rm -rf ${OUTPUT}
mkdir -p ${DIR}/../build/snap
cp -r ${PREFIX} ${OUTPUT}
