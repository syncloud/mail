#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=postfix
VERSION=3.4.10
OPENSSL_VERSION=1.0.2g
SASL_VERSION=2.1.27
BUILD_DIR=${DIR}/build
PREFIX=/snap/mail/current/${NAME}
echo "building ${NAME}"

apt update
apt -y install libdb-dev libldap2-dev libsasl2-dev m4

rm -rf ${BUILD_DIR}
mkdir -p ${BUILD_DIR}

cd ${BUILD_DIR}
wget https://github.com/cyrusimap/cyrus-sasl/releases/download/cyrus-sasl-${SASL_VERSION}/cyrus-sasl-${SASL_VERSION}.tar.gz
tar xf cyrus-sasl-${SASL_VERSION}.tar.gz
cd cyrus-sasl-${SASL_VERSION}
./configure \
    --prefix=${PREFIX} \
    --enable-static \
    --enable-shared \
    --enable-alwaystrue \
    --enable-checkapop \
    --enable-cram \
    --enable-digest \
    --enable-otp \
    --disable-srp \
    --disable-srp-setpass \
    --disable-krb4 \
    --enable-gss_mutexes \
    --enable-auth-sasldb \
    --enable-plain \
    --enable-anon \
    --enable-login \
    --enable-ntlm \
    --disable-passdss \
    --disable-macos-framework \
    --with-pam=/usr \
    --with-saslauthd=/var/snap/mail/common/saslauthd \
    --with-configdir=/snap/mail/current/postfix/lib/sasl2 \
    --with-plugindir=/snap/mail/current/postfix/lib/sasl2 \
    --sysconfdir=/snap/mail/current/postfix/config/sasl2 \
    --with-devrandom=/dev/urandom \
    --with-sphinx-build 
make
make install

cd ${BUILD_DIR}
curl -O https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz
tar xf openssl-${OPENSSL_VERSION}.tar.gz
cd openssl-${OPENSSL_VERSION}
./config --prefix=${PREFIX} --openssldir=/usr/lib/ssl no-shared no-ssl2 no-ssl3 -fPIC
make
make install

cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libldap*.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/liblber*.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libdb-*.so ${PREFIX}/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libnsl.so* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libresolv.so* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libdl.so* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libc.so* ${PREFIX}/lib
#cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgnutls-deb0.so* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libpthread.so.0 ${PREFIX}/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libz.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libp11-kit.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libtasn1.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libnettle.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libhogweed.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgmp.so* ${PREFIX}/lib
cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libffi.so* ${PREFIX}/lib
#cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libicui18n.so* ${PREFIX}/lib
#cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libicuuc.so* ${PREFIX}/lib
#cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libicudata.so* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libncurses.so* ${PREFIX}/lib
cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libpcre.so.* ${PREFIX}/lib
#cp /usr/lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libstdc++.so.* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libm.so.* ${PREFIX}/lib
#cp /lib/$(dpkg-architecture -q DEB_HOST_GNU_TYPE)/libgcc_s.so.* ${PREFIX}/lib

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

export AUXLIBS="-L${PREFIX}/lib -Wl,-rpath,$PREFIX/lib -lldap -llber -lssl -lcrypto -lsasl2"

make makefiles shared=no
make
make non-interactive-package install_root=${PREFIX}

ldd ${PREFIX}/usr/sbin/postfix
${PREFIX}/usr/sbin/postconf -a
${PREFIX}/usr/sbin/postconf -A
