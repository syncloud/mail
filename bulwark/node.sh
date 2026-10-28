#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

LIBS=$(echo \
  ${DIR}/lib \
  ${DIR}/lib/*-linux-gnu* \
  ${DIR}/usr/lib \
  ${DIR}/usr/lib/*-linux-gnu* | tr ' ' ':')

LOADER=$(ls \
  ${DIR}/lib/*-linux-gnu*/ld-linux*.so* \
  ${DIR}/lib/ld-linux*.so* \
  2>/dev/null | head -1)

exec "${LOADER}" --library-path "${LIBS}" ${DIR}/usr/local/bin/node "$@"
