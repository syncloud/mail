#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
SNAP_DIR=${DIR}/../build/snap

${SNAP_DIR}/bin/cli --help
for hook in install configure pre-refresh post-refresh; do
  ${SNAP_DIR}/meta/hooks/${hook} --help
done
