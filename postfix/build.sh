#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=postfix
VERSION=3.4.28
#OPENSSL_VERSION=1.1.0l
#SASL_VERSION=2.1.28
BUILD_DIR=${DIR}/build
PREFIX=/snap/mail/current/${NAME}
echo "building ${NAME}"

apt update
apt -y install libdb-dev libldap2-dev libsasl2-dev m4 wget build-essential curl libssl-dev libsasl2-dev

rm -rf ${BUILD_DIR}
mkdir -p ${BUILD_DIR}

#cd ${BUILD_DIR}
#wget https://github.com/cyrusimap/cyrus-sasl/releases/download/cyrus-sasl-${SASL_VERSION}/cyrus-sasl-${SASL_VERSION}.tar.gz
#tar xf cyrus-sasl-${SASL_VERSION}.tar.gz
#cd cyrus-sasl-${SASL_VERSION}
#./configure \
#    --enable-static \
#    --enable-shared \
#    --enable-alwaystrue \
#    --enable-checkapop \
#    --enable-cram \
#    --enable-digest \
#    --enable-otp \
#    --disable-srp \
#    --disable-srp-setpass \
#    --disable-krb4 \
#    --enable-gss_mutexes \
#    --enable-auth-sasldb \
#    --enable-plain \
#    --enable-anon \
#    --enable-login \
#    --enable-ntlm \
#    --disable-passdss \
#    --disable-macos-framework \
#    --with-pam=/usr \
#    --with-saslauthd=/var/snap/mail/common/saslauthd \
#    --with-configdir=/snap/mail/current/postfix/lib/sasl2 \
#    --with-plugindir=/snap/mail/current/postfix/lib/sasl2 \
#    --sysconfdir=/snap/mail/current/postfix/config/sasl2 \
#    --with-devrandom=/dev/urandom \
#    --with-sphinx-build
#make
#make install

#cd ${BUILD_DIR}
#curl -O https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz
#tar xf openssl-${OPENSSL_VERSION}.tar.gz
#cd openssl-${OPENSSL_VERSION}
#./config --prefix=${PREFIX} --openssldir=/usr/lib/ssl no-shared no-ssl2 no-ssl3 -fPIC
#./config --openssldir=/usr/lib/ssl no-shared no-ssl2 no-ssl3 -fPIC
#make
#make install

cd ${BUILD_DIR}
wget https://de.postfix.org/ftpmirror/official/${NAME}-${VERSION}.tar.gz --progress dot:giga
tar xf ${NAME}-${VERSION}.tar.gz
cd ${NAME}-${VERSION}
export CCARGS='-DDEF_CONFIG_DIR=\"/config/postfix\" \
  -DUSE_SASL_AUTH \
  -DDEF_SERVER_SASL_TYPE=\"dovecot\" \
  -I/include -I/usr/include \
  -DHAS_LDAP \
  -DUSE_TLS \
  -DUSE_CYRUS_SASL -I/usr/include/sasl'

LIBS=$(echo /lib/*-linux-gnu*)
USR_LIBS=$(echo /usr/lib/*-linux-gnu*)

#export AUXLIBS="-L${PREFIX}/lib -Wl,-rpath,$PREFIX/lib -lldap -llber -lssl -lcrypto -lsasl2"
export AUXLIBS="-L${USR_LIBS}/sasl -lsasl2 -L${LIBS} -lssl -lcrypto"
export AUXLIBS_LDAP="-L${LIBS} -lldap -llber"

make makefiles shared=no
make
make non-interactive-package install_root=${PREFIX}
#make non-interactive-package

# cleanup
apt-get -y purge build-essential
apt-get -y autoremove
rm -rf \
    /tmp/* \
    /var/lib/apt/lists/* \
    /var/tmp/* \
    /root/.cache

TARGET=${DIR}/../build/snap/postfix
mkdir $TARGET
cp -r /bin ${TARGET}
cp -r /sbin ${TARGET}
cp -r /lib* ${TARGET}
cp -r /usr/lib ${TARGET}
cp -r /usr/local/lib ${TARGET}
cp -r $PREFIX/* ${TARGET}

cp $DIR/postfix.sh ${TARGET}/bin
cp $DIR/postconf.sh ${TARGET}/bin
cp $DIR/postmap.sh ${TARGET}/bin

ldd ${TARGET}/usr/sbin/postfix
