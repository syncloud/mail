#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
RSPAMD=${DIR}/../build/snap/rspamd

${RSPAMD}/bin/rspamd.sh --version
${RSPAMD}/bin/rspamadm.sh --version
${RSPAMD}/bin/rspamc.sh --version

test -f ${RSPAMD}/etc/rspamd.conf
test -d ${RSPAMD}/share/lualib
test -d ${RSPAMD}/share/rules
test -d ${RSPAMD}/share/plugins
test -d ${RSPAMD}/share/www
