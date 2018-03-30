#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$2" ]]; then
    echo "usage $0 version installer"
    exit 1
fi

export TMPDIR=/tmp
export TMP=/tmp

NAME=mail
ROUNDCUBE_VERSION=1.3.4
ARCH=$(uname -m)
VERSION=$1
INSTALLER=$2

rm -rf ${DIR}/lib
mkdir ${DIR}/lib

coin --to lib py https://pypi.python.org/packages/2.7/r/requests/requests-2.7.0-py2.py3-none-any.whl
coin --to lib py https://pypi.python.org/packages/c8/c2/a670c1d6405f2ca67f87fd34391290db504217a7a77871811788e75331b6/syncloud-lib-44.tar.gz#md5=c792320a95912adb2263860df38a9102
coin --to lib py https://pypi.python.org/packages/source/t/tzlocal/tzlocal-1.2.2.tar.gz
coin --to lib py https://pypi.python.org/packages/source/p/pytz/pytz-2016.1.tar.gz

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
cd ${DIR}
cp -r ${DIR}/bin ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates
cp -r ${BUILD_DIR}/postfix/opt/data/mail/config/postfix/postfix-files ${BUILD_DIR}/config.templates/postfix
cp -r ${DIR}/lib ${BUILD_DIR}
cp -r ${DIR}/hooks ${BUILD_DIR}

mkdir build/${NAME}/META
echo ${NAME} > build/${NAME}/META/app
echo ${VERSION} > build/${NAME}/META/version

if [ $INSTALLER == "sam" ]; then

    echo "zipping"
    rm -rf ${NAME}*.tar.gz
    tar cpzf ${DIR}/${NAME}-${VERSION}-${ARCH}.tar.gz -C ${DIR}/build/ ${NAME}

else

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

    mksquashfs ${SNAP_DIR} ${DIR}/${NAME}_${VERSION}_${ARCH}.snap -noappend -comp xz -no-xattrs -all-root

fi