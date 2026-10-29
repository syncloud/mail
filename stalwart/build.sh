#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
VERSION=$1
WEBUI_VERSION=$2
SPAM_FILTER_VERSION=$3
BUILD_DIR=${DIR}/../build/snap/stalwart

case $(dpkg --print-architecture) in
  amd64) TARGET=x86_64-unknown-linux-musl ;;
  arm64) TARGET=aarch64-unknown-linux-musl ;;
  armhf) TARGET=armv7-unknown-linux-musleabihf ;;
esac

${DIR}/../apt.sh wget ca-certificates

mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}
wget --tries=5 --retry-connrefused --progress=dot:giga https://github.com/cyberb/stalwart/releases/download/${VERSION}/stalwart-${TARGET}.tar.gz
tar xf stalwart-${TARGET}.tar.gz
rm stalwart-${TARGET}.tar.gz
chmod +x stalwart
wget --tries=5 --retry-connrefused --progress=dot:giga -O webui.zip https://github.com/stalwartlabs/webui/releases/download/${WEBUI_VERSION}/webui.zip
wget --tries=5 --retry-connrefused --progress=dot:giga -O spam-filter-rules.json.gz https://github.com/stalwartlabs/spam-filter/releases/download/${SPAM_FILTER_VERSION}/spam-filter-rules.json.gz
ls -la ${BUILD_DIR}
