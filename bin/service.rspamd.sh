#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )

exec ${DIR}/rspamd/bin/rspamd.sh -f -c ${SNAP_DATA}/config/rspamd/rspamd.conf \
    --var=CONFDIR=${DIR}/rspamd/etc \
    --var=LOCAL_CONFDIR=${SNAP_DATA}/config/rspamd \
    --var=RUNDIR=${SNAP_DATA}/rspamd \
    --var=DBDIR=${SNAP_DATA}/rspamd \
    --var=LOGDIR=${SNAP_DATA}/log \
    --var=SHAREDIR=${DIR}/rspamd/share \
    --var=PLUGINSDIR=${DIR}/rspamd/share/plugins \
    --var=RULESDIR=${DIR}/rspamd/share/rules \
    --var=LUALIBDIR=${DIR}/rspamd/share/lualib \
    --var=WWWDIR=${DIR}/rspamd/share/www
