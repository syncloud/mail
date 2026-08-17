#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DOVECOT=${DIR}/../build/snap/dovecot

${DOVECOT}/bin/dovecot.sh --version
test -x ${DOVECOT}/bin/sievec

rm -rf /snap/mail/current
mkdir -p /snap/mail
ln -sfn ${DIR}/../build/snap /snap/mail/current

CHECK=$(mktemp -d)
sed -e "s|{{ .DataDir }}|${CHECK}|g" \
    -e "s|{{ .AppDir }}|${DIR}/..|g" \
    -e "s|{{ .DeviceDomainName }}|example.com|g" \
    ${DIR}/../config/dovecot/dovecot.conf > ${CHECK}/dovecot.conf

mkdir -p ${CHECK}/dovecot
${DOVECOT}/bin/doveconf.sh -c ${CHECK}/dovecot.conf > /dev/null
