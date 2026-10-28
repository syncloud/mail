#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
VERSION=$1
BUILD_DIR=${DIR}/../build/snap
APP_DIR=${BUILD_DIR}/bulwark
NODE_DIR=${BUILD_DIR}/node
SOCKET_DIR=${BUILD_DIR}/bulwark-socket
NATIVE_DIR=${DIR}/native

${DIR}/../apt.sh wget ca-certificates

rm -rf ${APP_DIR} ${NODE_DIR} ${SOCKET_DIR} ${NATIVE_DIR}
mkdir -p ${NODE_DIR} ${SOCKET_DIR} ${NATIVE_DIR}

cd ${DIR}
wget --tries=5 --retry-connrefused --progress=dot:giga https://github.com/bulwarkmail/webmail/releases/download/${VERSION}/bulwark-standalone-${VERSION}-linux-amd64.tar.gz
tar xf bulwark-standalone-${VERSION}-linux-amd64.tar.gz
rm bulwark-standalone-${VERSION}-linux-amd64.tar.gz
mv bulwark-standalone ${APP_DIR}
rm -rf ${APP_DIR}/.next/cache
ln -s /var/snap/mail/current/bulwark/cache ${APP_DIR}/.next/cache

SHARP_VERSION=$(node -p "require('${APP_DIR}/node_modules/sharp/package.json').version")
ESBUILD_VERSION=$(node -p "require('${APP_DIR}/node_modules/esbuild/package.json').version")
cd ${NATIVE_DIR}
npm init -y > /dev/null
npm install --no-audit --no-fund sharp@${SHARP_VERSION} esbuild@${ESBUILD_VERSION}
rm -rf ${APP_DIR}/node_modules/@img ${APP_DIR}/node_modules/sharp ${APP_DIR}/node_modules/@esbuild ${APP_DIR}/node_modules/esbuild
cp -r node_modules/@img node_modules/sharp node_modules/@esbuild node_modules/esbuild ${APP_DIR}/node_modules/

cd ${SOCKET_DIR}
npm init -y > /dev/null
npm install --no-audit --no-fund undici@6
cp ${DIR}/syncloud.js ${SOCKET_DIR}/index.js

cp -r /usr ${NODE_DIR}/usr
cp -r /lib ${NODE_DIR}/lib
cp ${DIR}/node.sh ${NODE_DIR}/node.sh

rm -rf ${NATIVE_DIR}
${NODE_DIR}/node.sh --version
du -sh ${APP_DIR} ${NODE_DIR} ${SOCKET_DIR}
