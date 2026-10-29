#!/bin/bash -e

DOMAIN=${1:?usage: wait-app.sh <domain>}
for attempt in $(seq 1 120); do
  if [[ "$(curl -skL -o /dev/null -w '%{http_code}' https://${DOMAIN}/)" == "200" ]]; then
    exit 0
  fi
  echo "waiting for ${DOMAIN} ${attempt}/120"
  sleep 5
done
echo "${DOMAIN} did not answer 200"
exit 1
