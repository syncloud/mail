#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
ROUNDCUBE_VERSION=$1
BUILD_DIR=${DIR}/build/snap
mkdir -p ${BUILD_DIR}

cd ${DIR}/build

apt update
apt -y install wget

wget --progress=dot:giga https://github.com/roundcube/roundcubemail/releases/download/${ROUNDCUBE_VERSION}/roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
tar xf roundcubemail-${ROUNDCUBE_VERSION}-complete.tar.gz
mv roundcubemail-${ROUNDCUBE_VERSION} ${BUILD_DIR}/roundcubemail
