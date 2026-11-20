#!/bin/bash -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

${DIR}/../apt.sh sshpass openssh-client netcat-openbsd curl expect telnet
pip install --retries 10 --timeout 60 -r ${DIR}/requirements.txt
