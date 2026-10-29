#!/bin/bash -e

set -a
. ${SNAP_DATA}/config/bulwark/bulwark.env
set +a

cd ${SNAP}/bulwark
exec ${SNAP}/node/node.sh --require ${SNAP}/bulwark-socket/index.js ${SNAP}/bulwark/server.js
