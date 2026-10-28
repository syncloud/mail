#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

SPEC=$1
DISTRO=$2
ARCH=$3
NAME=mail
DOMAIN=${DISTRO}.com
APP_DOMAIN=${NAME}.${DOMAIN}

APP_ARCHIVE_PATH=$(realpath $(cat ${DIR}/package.name))

cd ${DIR}/test
./deps.sh
py.test -x -s ${SPEC} --distro=${DISTRO} --domain=${DOMAIN} --app-archive-path=${APP_ARCHIVE_PATH} --device-host=${APP_DOMAIN} --app=${NAME} --arch=${ARCH}
