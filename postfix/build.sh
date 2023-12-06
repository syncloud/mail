#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=postfix
VERSION=3.4.28
OPENSSL_VERSION=1.0.2u
SASL_VERSION=2.1.28
BUILD_DIR=${DIR}/build
PREFIX=/snap/mail/current/${NAME}
echo "building ${NAME}"

apt update
apt -y install libdb-dev libldap2-dev libsasl2-dev m4 wget build-essential curl

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

cp /usr/lib/*/libldap*.so* ${PREFIX}/lib
cp /usr/lib/*/liblber*.so* ${PREFIX}/lib
cp /usr/lib/*/libdb-*.so ${PREFIX}/lib
cp /lib/*/libnsl.so* ${PREFIX}/lib
cp /lib/*/libresolv.so* ${PREFIX}/lib
cp /lib/*/libdl.so* ${PREFIX}/lib
cp /lib/*/libc.so* ${PREFIX}/lib
cp /usr/lib/*/libgnutls*.so* ${PREFIX}/lib
cp /usr/lib/*/libsasl2.so* ${PREFIX}/lib
cp /lib/*/libpthread.so* ${PREFIX}/lib
cp /lib/*/libz.so* ${PREFIX}/lib
cp /usr/lib/*/libp11-kit.so* ${PREFIX}/lib
cp /usr/lib/*/libtasn1.so* ${PREFIX}/lib
cp /usr/lib/*/libnettle.so* ${PREFIX}/lib
cp /usr/lib/*/libhogweed.so* ${PREFIX}/lib
cp /usr/lib/*/libgmp.so* ${PREFIX}/lib
cp /usr/lib/*/libffi.so* ${PREFIX}/lib
cp /usr/lib/*/libidn2.so* ${PREFIX}/lib
cp /usr/lib/*/libunistring.so* ${PREFIX}/lib
cp /lib/*/libpcre.so.* ${PREFIX}/lib
cp /lib/*/libgcc_s.so.* ${PREFIX}/lib
cp $(readlink -f /lib*/ld-linux-*.so*) ${PREFIX}/lib/ld.so

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

mkdir -p ${PREFIX}/bin
cp $DIR/postfix.sh ${PREFIX}/bin
cp $DIR/postconf.sh ${PREFIX}/bin
cp $DIR/postmap.sh ${PREFIX}/bin

ldd ${PREFIX}/usr/sbin/postfix

${PREFIX}/bin/postfix.sh --help || true
${PREFIX}/bin/postconf.sh -a
${PREFIX}/bin/postconf.sh -A

mv $PREFIX ${DIR}/../build/snap
