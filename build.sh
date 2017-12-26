#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

export TMPDIR=/tmp
export TMP=/tmp

NAME=mail
ROUNDCUBE_VERSION=1.3.3
ARCH=$(uname -m)
VERSION=$1

if [ -n "$DRONE" ]; then
    echo "running under drone, removing coin cache"
    rm -rf ${DIR}/.coin.cache
fi

rm -rf lib
mkdir lib

coin --to lib py https://pypi.python.org/packages/2.7/r/requests/requests-2.7.0-py2.py3-none-any.whl
coin --to lib py https://pypi.python.org/packages/ec/6b/b3fcd16215e3742c67a740fbb313e78f38741da5e40ee97681c9f9472aa5/syncloud-lib-27.tar.gz#md5=fa82721a7da75f570cd4ba8b4ce7a779
coin --to lib py https://pypi.python.org/packages/source/t/tzlocal/tzlocal-1.2.2.tar.gz
coin --to lib py https://pypi.python.org/packages/source/p/pytz/pytz-2016.1.tar.gz

cp -r ${DIR}/src lib/syncloud-mail-${VERSION}

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

DOWNLOAD_URL=http://artifact.syncloud.org/3rdparty

coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/postfix-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/dovecot-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/rsyslog-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/php7-${ARCH}.tar.gz
mv ${BUILD_DIR}/php7 ${BUILD_DIR}/php
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/nginx-${ARCH}.tar.gz
coin --to ${BUILD_DIR} raw ${DOWNLOAD_URL}/postgresql-${ARCH}.tar.gz

coin --to ${BUILD_DIR} raw https://github.com/roundcube/roundcubemail/releases/download/${ROUNDCUBE_VERSION}/roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
mv ${BUILD_DIR}/roundcubemail-${ROUNDCUBE_VERSION} ${BUILD_DIR}/roundcubemail
cd ${BUILD_DIR}/roundcubemail
patch -p0 < ${DIR}/patches/config-override.patch

#https://github.com/roundcube/roundcubemail/issues/5949
rm ${BUILD_DIR}/roundcubemail/vendor/pear/net_smtp/README.rst

cp -r ${DIR}/bin ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates
cp -r ${BUILD_DIR}/postfix/opt/data/mail/config/postfix/postfix-files ${BUILD_DIR}/config.templates/postfix
cp -r ${DIR}/lib ${BUILD_DIR}

mkdir build/${NAME}/META
echo ${NAME} > build/${NAME}/META/app
echo ${VERSION} > build/${NAME}/META/version

echo "zipping"
tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}
