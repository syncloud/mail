#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

if [[ -z "$1" ]]; then
    echo "usage $0 version"
    exit 1
fi

NAME=$1
ROUNDCUBE_VERSION=1.4.9
ARCH=$(uname -m)
VERSION=$2

apt update
apt -y install wget curl squashfs-tools dpkg-dev libltdl7

rm -rf ${DIR}/lib
mkdir ${DIR}/lib

rm -rf build
BUILD_DIR=${DIR}/build/${NAME}
mkdir -p ${BUILD_DIR}

${DIR}/postfix/build.sh
mv /snap/mail/current/postfix ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/dovecot-${ARCH}.tar.gz
tar xf dovecot-${ARCH}.tar.gz
mv dovecot ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/php7-${ARCH}.tar.gz
tar xf php7-${ARCH}.tar.gz
mv php ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/nginx-${ARCH}.tar.gz
tar xf nginx-${ARCH}.tar.gz
mv nginx ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/postgresql-${ARCH}.tar.gz
tar xf postgresql-${ARCH}.tar.gz
mv postgresql ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/python-${ARCH}.tar.gz
tar xf python-${ARCH}.tar.gz
mv python ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/opendkim-${ARCH}-2.10.3.tar.gz
tar xf opendkim-${ARCH}-2.10.3.tar.gz
mv opendkim ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/1/openssl-${ARCH}.tar.gz
tar xf openssl-${ARCH}.tar.gz
mv openssl integration/

${BUILD_DIR}/python/bin/pip install -r ${DIR}/requirements.txt

wget --progress=dot:giga https://github.com/roundcube/roundcubemail/releases/download/${ROUNDCUBE_VERSION}/roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
tar xf roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
mv roundcubemail-${ROUNDCUBE_VERSION} ${BUILD_DIR}/roundcubemail

cd ${BUILD_DIR}/roundcubemail
patch -p0 < ${DIR}/patches/roundcubemail.patch

cd ${DIR}
cp -r ${DIR}/bin ${BUILD_DIR}
cp -r ${DIR}/config ${BUILD_DIR}/config.templates
cp ${BUILD_DIR}/roundcubemail/config/defaults.inc.php ${BUILD_DIR}/config.templates/roundcube/
cp -r ${BUILD_DIR}/postfix/config/postfix/postfix-files ${BUILD_DIR}/config.templates/postfix
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
