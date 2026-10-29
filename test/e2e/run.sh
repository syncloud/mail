#!/bin/bash -e
DIR=$(cd "$(dirname "$0")" && pwd)
cd "$DIR"

SPEC=${1:?usage: run.sh <spec> <project>}
PROJECT=${2:?usage: run.sh <spec> <project>}

export PLAYWRIGHT_FULL_DOMAIN=bookworm.com
export PLAYWRIGHT_APP_DOMAIN=mail.bookworm.com
export PLAYWRIGHT_DEVICE_HOST=mail.bookworm.com
export PLAYWRIGHT_DEVICE_USER=user
export PLAYWRIGHT_DEVICE_PASSWORD=Password1
export PLAYWRIGHT_SSH_USER=root
export PLAYWRIGHT_SSH_PASSWORD=Password1
export PLAYWRIGHT_PROJECT=${PROJECT}
export PLAYWRIGHT_ARTIFACT_DIR=/drone/src/artifact/screenshots

${DIR}/../../apt.sh sshpass openssh-client curl
getent hosts "${PLAYWRIGHT_APP_DOMAIN}" | sed "s/${PLAYWRIGHT_APP_DOMAIN}/auth.${PLAYWRIGHT_FULL_DOMAIN}/g" | tee -a /etc/hosts
${DIR}/wait-app.sh ${PLAYWRIGHT_APP_DOMAIN}
npm ci --no-audit --no-fund
npx playwright test --project="${PROJECT}" "$SPEC"
