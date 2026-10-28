#!/bin/bash -e

set -a
. ${SNAP_DATA}/config/stalwart/stalwart.env
set +a

exec ${SNAP}/stalwart/stalwart -c ${SNAP_DATA}/config/stalwart/config.json
