#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp
NAME=nginx
VERSION=1.20.1
OPENSSL_VERSION=1.1.1
PCRE_VERSION=8.40
PREFIX=${DIR}/../build/snap/nginx

apt-get update
apt-get -y install build-essential flex bison libreadline-dev zlib1g-dev wget

rm -rf ${DIR}/work
mkdir -p ${DIR}/work
cd ${DIR}/work

wget http://nginx.org/download/${NAME}-${VERSION}.tar.gz --progress dot:giga
tar xzf ${NAME}-${VERSION}.tar.gz

wget http://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz --progress dot:giga
tar xzf openssl-${OPENSSL_VERSION}.tar.gz

wget https://downloads.sourceforge.net/project/pcre/pcre/${PCRE_VERSION}/pcre-${PCRE_VERSION}.tar.gz --progress dot:giga
tar xzf pcre-${PCRE_VERSION}.tar.gz

CC_OPT="-static -static-libgcc"
OPENSSL_OPT="no-asm"
if [ "$(dpkg --print-architecture)" = "armhf" ]; then
    CC_OPT="${CC_OPT} -mfpu=vfpv3-d16"
    OPENSSL_OPT="${OPENSSL_OPT} -mfpu=vfpv3-d16"
fi

cd ${NAME}-${VERSION}
./configure --prefix=${PREFIX} \
    --with-cpu-opt=generic \
    --with-cc-opt="${CC_OPT}" \
    --with-ld-opt="-static" \
    --with-http_ssl_module \
    --with-http_gzip_static_module \
    --with-openssl=../openssl-${OPENSSL_VERSION} \
    --with-pcre=../pcre-${PCRE_VERSION} \
    --with-http_realip_module \
    --with-http_v2_module \
    --with-openssl-opt="${OPENSSL_OPT}"

sed -i "/CFLAGS/s/ \-O //g" objs/Makefile

make -j1
rm -rf ${PREFIX}
make install
