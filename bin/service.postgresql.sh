#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

exec ${DIR}/postgresql/bin/pg_ctl.sh -w -s -D ${SNAP_DATA}/database start
