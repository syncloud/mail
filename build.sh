#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$1" ]]; then
    echo "usage $0 version"
    exit 1
fi

export TMPDIR=/tmp
export TMP=/tmp

NAME=$1
ROUNDCUBE_VERSION=1.4.0
ARCH=$(uname -m)
VERSION=$2

rm -rf ${DIR}/lib
mkdir ${DIR}/lib

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/postfix-${ARCH}.tar.gz
tar xf postfix-${ARCH}.tar.gz
mv postfix ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/dovecot-${ARCH}.tar.gz
tar xf dovecot-${ARCH}.tar.gz
mv dovecot ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/rsyslog-${ARCH}.tar.gz
tar xf rsyslog-${ARCH}.tar.gz
mv rsyslog ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/php7-${ARCH}.tar.gz
tar xf php7-${ARCH}.tar.gz
mv php7 ${BUILD_DIR}/php

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/nginx-${ARCH}.tar.gz
tar xf nginx-${ARCH}.tar.gz
mv nginx ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/postgresql-${ARCH}.tar.gz
tar xf postgresql-${ARCH}.tar.gz
mv postgresql ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/python-${ARCH}.tar.gz
tar xf python-${ARCH}.tar.gz
mv python ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/opendkim-${ARCH}.tar.gz
tar xf opendkim-${ARCH}.tar.gz
mv opendkim ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/openssl-${ARCH}.tar.gz
tar xf openssl-${ARCH}.tar.gz
mv openssl integration/

${BUILD_DIR}/python/bin/pip install -r ${DIR}/requirements.txt

coin --to ${BUILD_DIR} raw https://github.com/roundcube/roundcubemail/releases/download/${ROUNDCUBE_VERSION}/roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
mv ${BUILD_DIR}/roundcubemail-${ROUNDCUBE_VERSION} ${BUILD_DIR}/roundcubemail

cd ${BUILD_DIR}/roundcubemail
patch -p0 < ${DIR}/patches/roundcubemail.patch

cd ${DIR}
cp -r ${DIR}/bin ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates
cp -r ${BUILD_DIR}/postfix/opt/data/mail/config/postfix/postfix-files ${BUILD_DIR}/config.templates/postfix
cp -r ${DIR}/lib ${BUILD_DIR}
cp -r ${DIR}/hooks ${BUILD_DIR}

mkdir build/${NAME}/META
echo ${NAME} > build/${NAME}/META/app
echo ${VERSION} > build/${NAME}/META/version

echo "snapping"
SNAP_DIR=${DIR}/build/snap
ARCH=$(dpkg-architecture -q DEB_HOST_ARCH)
rm -rf ${DIR}/*.snap
mkdir ${SNAP_DIR}
cp -r ${BUILD_DIR}/* ${SNAP_DIR}/
cp -r ${DIR}/snap/meta ${SNAP_DIR}/
cp ${DIR}/snap/snap.yaml ${SNAP_DIR}/meta/snap.yaml
echo "version: $VERSION" >> ${SNAP_DIR}/meta/snap.yaml
echo "architectures:" >> ${SNAP_DIR}/meta/snap.yaml
echo "- ${ARCH}" >> ${SNAP_DIR}/meta/snap.yaml

PACKAGE=${NAME}_${VERSION}_${ARCH}.snap
echo ${PACKAGE} > ${DIR}/package.name
mksquashfs ${SNAP_DIR} ${DIR}/${PACKAGE} -noappend -comp xz -no-xattrs -all-root
