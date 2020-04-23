#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=postfix
VERSION=3.4.10
OPENSSL_VERSION=1.0.2g
BUILD_DIR=${DIR}/build
PREFIX=/snap/mail/current/${NAME}
echo "building ${NAME}"

rm -rf ${BUILD_DIR}
mkdir -p ${BUILD_DIR}

cd ${BUILD_DIR}
curl -O https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz
tar xf openssl-${OPENSSL_VERSION}.tar.gz
cd openssl-${OPENSSL_VERSION}
./config --prefix=${PREFIX} --openssldir=/usr/lib/ssl no-shared no-ssl2 no-ssl3 -fPIC
make
make install

ls -la ${PREFIX}/lib
ls -la ${PREFIX}/include

cd ${BUILD_DIR}
wget https://de.postfix.org/ftpmirror/official/${NAME}-${VERSION}.tar.gz --progress dot:giga
tar xf ${NAME}-${VERSION}.tar.gz
cd ${NAME}-${VERSION}
export CCARGS='-DDEF_CONFIG_DIR=\"/config/postfix\" \
	-DUSE_SASL_AUTH \
	-DDEF_SERVER_SASL_TYPE=\"dovecot\" \
  -I'${PREFIX}'/include -I/usr/include -DHAS_LDAP \
  -DUSE_TLS \
 	-DUSE_CYRUS_SASL -I/usr/include/sasl'

export AUXLIBS="-L${PREFIX}/lib \
  -L/usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE) \
  -lldap -L/usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE) \
  -llber -lssl -lcrypto -lsasl2"

make makefiles
make
make non-interactive-package install_root=${PREFIX}

mv ${PREFIX}/usr/sbin/postfix ${PREFIX}/usr/sbin/postfix.bin
mv ${PREFIX}/usr/sbin/postconf ${PREFIX}/usr/sbin/postconf.bin
mv ${PREFIX}/usr/sbin/postlog ${PREFIX}/usr/sbin/postlog.bin
mv ${PREFIX}/usr/sbin/postsuper ${PREFIX}/usr/sbin/postsuper.bin
mv ${PREFIX}/usr/sbin/postalias ${PREFIX}/usr/sbin/postalias.bin
mv ${PREFIX}/usr/sbin/postcat ${PREFIX}/usr/sbin/postcat.bin
mv ${PREFIX}/usr/sbin/postdrop ${PREFIX}/usr/sbin/postdrop.bin
mv ${PREFIX}/usr/sbin/postkick ${PREFIX}/usr/sbin/postkick.bin
mv ${PREFIX}/usr/sbin/postlock ${PREFIX}/usr/sbin/postlock.bin
mv ${PREFIX}/usr/sbin/postmap ${PREFIX}/usr/sbin/postmap.bin
mv ${PREFIX}/usr/sbin/postmulti ${PREFIX}/usr/sbin/postmulti.bin
mv ${PREFIX}/usr/sbin/postqueue ${PREFIX}/usr/sbin/postqueue.bin
mv ${PREFIX}/usr/sbin/sendmail ${PREFIX}/usr/sbin/sendmail.bin

mv ${PREFIX}/usr/libexec/postfix/master ${PREFIX}/usr/libexec/postfix/master.bin

cp ${DIR}/usr/sbin/* ${PREFIX}/usr/sbin
cp ${DIR}/usr/libexec/postfix/* ${PREFIX}/usr/libexec/postfix

echo "original libs"
ldd ${PREFIX}/usr/sbin/postfix.bin
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libldap*.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/liblber*.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libdb-*.so ${PREFIX}/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libnsl.so* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libresolv.so* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libdl.so* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libc.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libsasl2.so* ${PREFIX}/lib
cp -r /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/sasl2 ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgnutls-deb0.so* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libpthread.so.0 ${PREFIX}/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libz.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libp11-kit.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libtasn1.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libnettle.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libhogweed.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgmp.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libffi.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libicui18n.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libicuuc.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libicudata.so* ${PREFIX}/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libncurses.so* ${PREFIX}/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libpcre.so.* ${PREFIX}/lib 
#cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libstdc++.so.* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libm.so.* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgcc_s.so.* ${PREFIX}/lib 

echo "embedded libs"
#export LD_DEBUG=libs
export LD_LIBRARY_PATH=${PREFIX}/lib
#export LD_PRELOAD=${PREFIX}/lib
ldd ${PREFIX}/usr/sbin/postfix.bin
ldd ${PREFIX}/usr/sbin/postconf.bin
ldd ${PREFIX}/usr/sbin/postlog.bin
ldd ${PREFIX}/usr/libexec/postfix/master.bin

${PREFIX}/usr/sbin/postconf -a
${PREFIX}/usr/sbin/postconf -A
