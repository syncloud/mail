#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DOWNLOAD_URL=https://github.com/syncloud/3rdparty/releases/download
ROUNDCUBE_VERSION=$1
ARCH=$(uname -m)
rm -rf ${DIR}/build
BUILD_DIR=${DIR}/build/snap
mkdir -p ${BUILD_DIR}

cd ${DIR}/build

apt update
apt -y install wget unzip

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/dovecot/dovecot-${ARCH}.tar.gz
tar xf dovecot-${ARCH}.tar.gz
mv dovecot ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/nginx/nginx-${ARCH}.tar.gz
tar xf nginx-${ARCH}.tar.gz
mv nginx ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/opendkim/opendkim-${ARCH}.tar.gz
tar xf opendkim-${ARCH}.tar.gz
mv opendkim ${BUILD_DIR}

wget --progress=dot:giga https://github.com/syncloud/3rdparty/releases/download/openssl/openssl-${ARCH}.tar.gz
tar xf openssl-${ARCH}.tar.gz
mv openssl integration/

wget --progress=dot:giga https://github.com/roundcube/roundcubemail/releases/download/${ROUNDCUBE_VERSION}/roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
tar xf roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
mv roundcubemail-${ROUNDCUBE_VERSION} ${BUILD_DIR}/roundcubemail
