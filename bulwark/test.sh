#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
NODE=${DIR}/../build/snap/node/node.sh
APP=${DIR}/../build/snap/bulwark

${NODE} --version
cd ${APP}
${NODE} -e "require('sharp'); require('esbuild'); console.log('native modules load ok')"
${NODE} -e "require(process.argv[1]); console.log('socket preload loads ok')" ${DIR}/../build/snap/bulwark-socket/index.js
