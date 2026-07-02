#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${DIR}

${DIR}/../build/snap/nginx/sbin/nginx -version
