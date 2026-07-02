#!/bin/sh -xe

DIR=$( cd "$( dirname "$0" )" && pwd )
cd ${DIR}

BUILD_DIR=${DIR}/../build/snap/php
${BUILD_DIR}/bin/php.sh -i
${BUILD_DIR}/bin/php.sh -m
${BUILD_DIR}/bin/php-fpm.sh -v
