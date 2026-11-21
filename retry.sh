#!/bin/bash -e

for i in $(seq 1 10); do
  if "$@"; then
    exit 0
  fi
  echo "retry $*"
  sleep 10
done

echo "failed $*"
exit 1
