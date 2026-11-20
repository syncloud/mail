#!/bin/bash -e

URL=${1:?usage: download.sh <url> <target>}
TARGET=${2:?usage: download.sh <url> <target>}

for i in $(seq 1 10); do
  if wget --tries=3 --timeout=60 --progress=dot:giga -O "${TARGET}" "${URL}"; then
    exit 0
  fi
  echo "retry download"
  sleep 10
done

echo "download failed"
exit 1
