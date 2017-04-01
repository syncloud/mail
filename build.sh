#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp

NAME=mail
ROUNDCUBE_VERSION=1.1.4

apt-get install -y git build-essential dpkg-dev

ARCH=$(dpkg-architecture -qDEB_HOST_GNU_CPU)
if [ ! -z "$1" ]; then
    ARCH=$1
fi

VERSION="local"
if [ ! -z "$2" ]; then
    VERSION=$2
fi

wget --no-check-certificate --progress=dot:giga -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py 2>&1
python /tmp/get-pip.py
pip install coin

./coin_lib.sh

cp -r ${DIR}/src lib/syncloud-mail-${VERSION}

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://build.syncloud.org:8111/guestAuth/repository/download

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_postfix_${ARCH}/lastSuccessful/postfix-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_dovecot_${ARCH}/lastSuccessful/dovecot-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_rsyslog_${ARCH}/lastSuccessful/rsyslog-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_php_${ARCH}/lastSuccessful/php-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_nginx_${ARCH}/lastSuccessful/nginx-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/thirdparty_postgresql_${ARCH}/lastSuccessful/postgresql-${ARCH}.tar.gz

coin --to ${BUILD_DIR} raw https://downloads.sourceforge.net/project/roundcubemail/roundcubemail/${ROUNDCUBE_VERSION}/roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz

mv ${BUILD_DIR}/roundcubemail-${ROUNDCUBE_VERSION} ${BUILD_DIR}/roundcubemail

cp ${DIR}/config/postgresql/postgresql.conf ${BUILD_DIR}/postgresql/share/postgresql.conf.sample

cp -r bin ${BUILD_DIR}
cp -r config ${BUILD_DIR}
cp -r lib ${BUILD_DIR}

mkdir build/${NAME}/META
echo ${NAME} >> build/${NAME}/META/app
echo ${VERSION} >> build/${NAME}/META/version

echo "zipping"
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}
