#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
exec $DIR/webui unix ${SNAP_COMMON}/webui.socket
