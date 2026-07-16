#!/bin/bash -e
DIR=$(cd "$(dirname "$0")" && pwd)
cd "$DIR"

ARTIFACT_SUBDIR=$1
SPEC=$2
PROJECT=${3:-desktop}

export PLAYWRIGHT_FULL_DOMAIN=bookworm.com
export PLAYWRIGHT_APP_DOMAIN=mail.bookworm.com
export PLAYWRIGHT_DEVICE_HOST=mail.bookworm.com
export PLAYWRIGHT_DEVICE_USER=user
export PLAYWRIGHT_DEVICE_PASSWORD=Password1
export PLAYWRIGHT_SSH_USER=root
export PLAYWRIGHT_SSH_PASSWORD=Password1
export PLAYWRIGHT_PROJECT=${PROJECT}
export PLAYWRIGHT_ARTIFACT_DIR=/drone/src/artifact/${ARTIFACT_SUBDIR}
export PLAYWRIGHT_MAILPIT_URL=http://mailpit:8025
export PLAYWRIGHT_RELAY_HOST=mailpit
export PLAYWRIGHT_RELAY_PORT=1025
export PLAYWRIGHT_RELAY_USER=relayuser
export PLAYWRIGHT_RELAY_PASSWORD=relaypass

apt-get update -qq
apt-get install -y -qq sshpass openssh-client curl
npm ci --no-audit --no-fund
npx playwright test --project="${PROJECT}" "$SPEC"
